from . import lpr_api, lpr_config

PluginInfo = {
    "group": "ocr",
    "api_class": lpr_api.Api,
    "global_options": lpr_config.globalOptions,
    "local_options": lpr_config.localOptions,
}
