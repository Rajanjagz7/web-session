package com.rajan

import android.content.Context
import com.lagradost.cloudstream3.plugins.CloudstreamPlugin
import com.lagradost.cloudstream3.plugins.Plugin

@CloudstreamPlugin
class RajanTVPlugin : Plugin() {
    override fun load(context: Context) {
        registerMainAPI(RajanTV())
    }
}
