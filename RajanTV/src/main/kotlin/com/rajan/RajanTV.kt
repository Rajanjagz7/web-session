package com.rajan

import com.lagradost.cloudstream3.*
import com.lagradost.cloudstream3.utils.*
import com.lagradost.cloudstream3.utils.AppUtils.toJson
import com.lagradost.cloudstream3.utils.AppUtils.tryParseJson

/**
 * Free Indian live TV from the public iptv-org playlists (https://github.com/iptv-org/iptv).
 * Home rows are built from each channel's category (group-title) or from a language playlist.
 */
class RajanTV : MainAPI() {
    override var mainUrl = "https://iptv-org.github.io/iptv"
    override var name = "Rajan Live TV"
    override var lang = "hi"
    override val hasMainPage = true
    override val hasQuickSearch = true
    override val supportedTypes = setOf(TvType.Live)

    data class Channel(
        val name: String,
        val url: String,
        val logo: String? = null,
        val groups: List<String> = emptyList(),
        val referer: String? = null,
        val userAgent: String? = null,
    )

    // row data = "<playlist path>|<category filter, ; separated, or *>"
    override val mainPage = mainPageOf(
        "countries/in.m3u|News" to "📰 News 24x7",
        "countries/in.m3u|Entertainment;General;Series" to "🎭 Entertainment",
        "countries/in.m3u|Movies" to "🎬 Movie Channels",
        "countries/in.m3u|Music" to "🎵 Music",
        "countries/in.m3u|Religious" to "🙏 Devotional",
        "countries/in.m3u|Kids;Animation;Family" to "🧸 Kids & Family",
        "countries/in.m3u|Sports" to "🏏 Sports",
        "countries/in.m3u|Education;Documentary;Science;Culture" to "📚 Learn & Explore",
        "languages/hin.m3u|*" to "🇮🇳 Hindi",
        "languages/guj.m3u|*" to "🪁 Gujarati",
        "languages/mar.m3u|*" to "🏵️ Marathi",
        "languages/tam.m3u|*" to "🛕 Tamil",
        "languages/tel.m3u|*" to "🎞️ Telugu",
        "languages/ben.m3u|*" to "🐟 Bengali",
        "languages/pan.m3u|*" to "🌾 Punjabi",
        "languages/mal.m3u|*" to "🌴 Malayalam",
        "languages/kan.m3u|*" to "🏯 Kannada",
        "countries/in.m3u|*" to "📺 All Indian Channels",
    )

    private val cache = mutableMapOf<String, List<Channel>>()

    private suspend fun playlist(path: String): List<Channel> {
        cache[path]?.let { return it }
        val text = try {
            app.get("$mainUrl/$path").text
        } catch (e: Exception) {
            return emptyList()
        }
        val parsed = parseM3u(text)
        if (parsed.isNotEmpty()) cache[path] = parsed
        return parsed
    }

    private fun attr(line: String, key: String): String? =
        Regex("$key=\"([^\"]*)\"").find(line)?.groupValues?.get(1)?.takeIf { it.isNotBlank() }

    private fun parseM3u(text: String): List<Channel> {
        val out = ArrayList<Channel>()
        var info: String? = null
        var referer: String? = null
        var ua: String? = null
        for (raw in text.lineSequence()) {
            val line = raw.trim()
            if (line.startsWith("#EXTINF")) {
                info = line; referer = null; ua = null
            } else if (line.startsWith("#EXTVLCOPT:http-referrer=")) {
                referer = line.substringAfter("=")
            } else if (line.startsWith("#EXTVLCOPT:http-user-agent=")) {
                ua = line.substringAfter("=")
            } else if (line.isNotEmpty() && !line.startsWith("#")) {
                val inf = info ?: continue
                val title = inf.substringAfterLast(",").trim()
                    .replace(Regex("\\s*\\[(Geo-blocked|Not 24/7)]"), "")
                    .replace(Regex("\\s*\\(\\d{3,4}p\\)"), "")
                    .trim()
                val groups = (attr(inf, "group-title") ?: "Undefined").split(";").map { it.trim() }
                if (title.isNotEmpty()) out.add(Channel(title, line, attr(inf, "tvg-logo"), groups, referer, ua))
                info = null
            }
        }
        // the same channel can be listed in several qualities - keep the first of each name
        return out.distinctBy { it.name.lowercase() }
    }

    private fun Channel.toSearch(): SearchResponse =
        newLiveSearchResponse(name, this.toJson(), TvType.Live, fix = false) {
            this.posterUrl = logo
        }

    override suspend fun getMainPage(page: Int, request: MainPageRequest): HomePageResponse? {
        if (page > 1) return newHomePageResponse(request, emptyList(), false)
        val path = request.data.substringBefore("|")
        val filter = request.data.substringAfter("|")
        val wanted = filter.split(";").map { it.trim() }
        val list = playlist(path).filter { ch -> filter == "*" || ch.groups.any { it in wanted } }
        return newHomePageResponse(
            HomePageList(request.name, list.map { it.toSearch() }, isHorizontalImages = true),
            hasNext = false
        )
    }

    override suspend fun search(query: String): List<SearchResponse> {
        val q = query.trim().lowercase()
        if (q.isEmpty()) return emptyList()
        return playlist("countries/in.m3u").filter { it.name.lowercase().contains(q) }.map { it.toSearch() }
    }

    override suspend fun quickSearch(query: String): List<SearchResponse> = search(query)

    override suspend fun load(url: String): LoadResponse? {
        val ch = tryParseJson<Channel>(url) ?: return null
        return newLiveStreamLoadResponse(ch.name, url, url) {
            this.posterUrl = ch.logo
            this.tags = ch.groups.filter { it != "Undefined" }
            this.plot = "Free live channel · " + ch.groups.joinToString(" · ") +
                "\nSource: public iptv-org playlist. Some channels may be offline or region-locked."
        }
    }

    override suspend fun loadLinks(
        data: String,
        isCasting: Boolean,
        subtitleCallback: (SubtitleFile) -> Unit,
        callback: (ExtractorLink) -> Unit
    ): Boolean {
        val ch = tryParseJson<Channel>(data) ?: return false
        val isHls = ch.url.contains(".m3u8", ignoreCase = true)
        callback(
            newExtractorLink(
                source = name,
                name = ch.name,
                url = ch.url,
                type = if (isHls) ExtractorLinkType.M3U8 else ExtractorLinkType.VIDEO
            ) {
                this.referer = ch.referer ?: ""
                this.quality = Qualities.Unknown.value
                val agent = ch.userAgent
                if (agent != null) this.headers = mapOf("User-Agent" to agent)
            }
        )
        return true
    }
}
