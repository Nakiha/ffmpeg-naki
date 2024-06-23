#include <napi.h>
extern "C" {
  #include "libavutil/log.h"
}

class HelloAddon : public Napi::Addon<HelloAddon> {
public:
  HelloAddon(Napi::Env env, Napi::Object exports) {
    DefineAddon(exports,
      {InstanceMethod("hello", &HelloAddon::Hello, napi_enumerable)});
  }

private:
  Napi::Value Hello(const Napi::CallbackInfo& info) {
    av_log_set_level(AV_LOG_DEBUG);
    av_log(NULL, AV_LOG_DEBUG, "%s", "HELLO FFMPEG\n");
    return Napi::String::New(info.Env(), "world");
  }
};

NODE_API_ADDON(HelloAddon)