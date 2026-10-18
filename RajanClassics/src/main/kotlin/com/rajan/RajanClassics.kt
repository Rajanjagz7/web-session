package com.rajan

import com.fasterxml.jackson.databind.JsonNode
import com.lagradost.cloudstream3.*
import com.lagradost.cloudstream3.utils.*
import java.net.URLEncoder

/**
 * Public-domain and openly licensed classic films from the Internet Archive (https://archive.org).
 */
class RajanClassics : MainAPI() {
    override var mainUrl = "https://archive.org"
    override var name = "Rajan Classics"
    override var lang = "en"
    override val hasMainPage = true
    override val supportedTypes = setOf(TvType.Movie)

    private val films = "mediatype:movies AND collection:feature_films"

    override val mainPage = mainPageOf(
        films to "🔥 Most Watched Classics",
        "mediatype:movies AND collection:film_noir" to "🕵️ Film Noir",
        "mediatype:movies AND collection:SciFi_Horror" to "👽 Sci-Fi & Horror",
        "$films AND subject:(comedy)" to "😂 Comedy Classics",
        "$films AND subject:(western)" to "🤠 Westerns",
        "$films AND subject:(crime OR mystery OR thriller)" to "🔪 Crime & Mystery",
        "$films AND subject:(war)" to "🎖️ War Films",
        "$films AND subject:(romance OR drama)" to "💘 Romance & Drama",
        "mediatype:movies AND collection:silent_films" to "🎩 Silent Era",
        "mediatype:movies AND collection:classic_cartoons" to "🐭 Classic Cartoons",
        "mediatype:movies AND collection:prelinger" to "📽️ Vintage Americana",
    )

    private fun enc(s: String): String = URLEncoder.encode(s, "UTF-8")

    private fun encPath(p: String): String = p.split("/").joinToString("/") { enc(it).replace("+", "%20") }

    private fun poster(id: String) = "$mainUrl/services/img/$id"

    private fun JsonNode?.str(): String? {
        if (this == null || isNull || isMissingNode) return null
        val v = if (isArray) (if (size() > 0) get(0).asText() else null) else asText()
        return v?.takeIf { it.isNotBlank() }
    }

    private suspend fun searchDocs(q: String, page: Int, rows: Int = 30): List<JsonNode> {
        val url = "$mainUrl/advancedsearch.php?q=" + enc("($q) AND -access-restricted-item:true") +
            "&fl[]=identifier&fl[]=title&fl[]=year&sort[]=" + enc("downloads desc") +
            "&rows=$rows&page=$page&output=json"
        return try {
            mapper.readTree(app.get(url).text).path("response").path("docs").toList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun JsonNode.toSearch(): SearchResponse? {
        val id = path("identifier").str() ?: return null
        val title = path("title").str() ?: id
        val yr = path("year").str()?.take(4)?.toIntOrNull()
        return newMovieSearchResponse(title, "$mainUrl/details/$id", TvType.Movie) {
            this.posterUrl = poster(id)
            this.year = yr
        }
    }

    override suspend fun getMainPage(page: Int, request: MainPageRequest): HomePageResponse? {
        val list = searchDocs(request.data, page).mapNotNull { it.toSearch() }
        return newHomePageResponse(request, list, hasNext = list.size >= 30)
    }

    override suspend fun search(query: String): List<SearchResponse> {
        val q = query.replace("\"", "").trim()
        if (q.isEmpty()) return emptyList()
        val scope = "mediatype:movies AND (collection:feature_films OR collection:film_noir OR " +
            "collection:SciFi_Horror OR collection:silent_films OR collection:classic_cartoons)"
        return searchDocs("$scope AND title:(\"$q\")", 1, 40).mapNotNull { it.toSearch() }
    }

    private suspend fun meta(id: String): JsonNode? =
        try {
            mapper.readTree(app.get("$mainUrl/metadata/$id").text)
        } catch (e: Exception) {
            null
        }

    override suspend fun load(url: String): LoadResponse? {
        val id = url.substringAfter("/details/").substringBefore("/").substringBefore("?")
        val m = meta(id) ?: return null
        val md = m.path("metadata")
        if (md.isMissingNode) return null
        val title = md.path("title").str() ?: id
        val description = md.path("description").str()
            ?.replace(Regex("<br\\s*/?>", RegexOption.IGNORE_CASE), "\n")
            ?.replace(Regex("<[^>]+>"), "")
            ?.replace("&nbsp;", " ")?.replace("&amp;", "&")
            ?.trim()
        val yr = (md.path("year").str() ?: md.path("date").str())?.take(4)?.toIntOrNull()
        val subj = md.path("subject")
        val subjects: List<String> =
            if (subj.isArray) subj.map { it.asText() } else (subj.str()?.split(";", ",") ?: emptyList())
        val tagList = subjects.map { it.trim() }.filter { it.isNotEmpty() }.take(8)
        val mins = md.path("runtime").str()?.let { r ->
            val p = r.split(":").mapNotNull { it.trim().toIntOrNull() }
            when (p.size) {
                3 -> p[0] * 60 + p[1]
                2 -> p[0]
                else -> r.filter { it.isDigit() }.toIntOrNull()
            }
        }
        return newMovieLoadResponse(title, url, TvType.Movie, id) {
            this.posterUrl = poster(id)
            this.plot = description
            this.year = yr
            this.tags = tagList
            this.duration = mins
        }
    }

    override suspend fun loadLinks(
        data: String,
        isCasting: Boolean,
        subtitleCallback: (SubtitleFile) -> Unit,
        callback: (ExtractorLink) -> Unit
    ): Boolean {
        val m = meta(data) ?: return false
        val files = m.path("files").toList()
        val rank = listOf("h.264 HD", "h.264", "MPEG4", "512Kb MPEG4", "h.264 IA")
        val videos = files
            .filter { it.path("name").asText().endsWith(".mp4", ignoreCase = true) }
            .sortedWith(
                compareBy<JsonNode>({ rank.indexOf(it.path("format").asText()).let { i -> if (i < 0) 99 else i } })
                    .thenByDescending { it.path("size").asText().toLongOrNull() ?: 0L }
            )
            .take(4)
        for (f in videos) {
            val fileName = f.path("name").asText()
            val fmt = f.path("format").asText().ifBlank { "MP4" }
            val h = f.path("height").asText().toIntOrNull()
            callback(
                newExtractorLink(name, "$name · $fmt", "$mainUrl/download/$data/${encPath(fileName)}", ExtractorLinkType.VIDEO) {
                    this.quality = h ?: if (fmt.contains("HD")) Qualities.P720.value else Qualities.P480.value
                    this.referer = "$mainUrl/"
                }
            )
        }
        for (f in files) {
            val n = f.path("name").asText()
            if (n.endsWith(".srt", true) || n.endsWith(".vtt", true)) {
                subtitleCallback(newSubtitleFile("English", "$mainUrl/download/$data/${encPath(n)}"))
            }
        }
        return videos.isNotEmpty()
    }
}
