/**
 * NakiParser - Video Stream Parser Library
 *
 * 静态链接FFmpeg，支持多种编码格式的码流分析
 * 避免与系统其他FFmpeg库符号冲突
 */

#ifndef NAKI_PARSER_H
#define NAKI_PARSER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 版本 */
#define NAKI_PARSER_VERSION_MAJOR 1
#define NAKI_PARSER_VERSION_MINOR 0
#define NAKI_PARSER_VERSION_PATCH 0

#define NAKI_PARSER_VERSION \
    ((NAKI_PARSER_VERSION_MAJOR << 16) | (NAKI_PARSER_VERSION_MINOR << 8) | NAKI_PARSER_VERSION_PATCH)

/* 导出宏 */
#ifdef NAKI_PARSER_BUILD
    #ifdef _WIN32
        #define NAKI_API __declspec(dllexport)
    #else
        #define NAKI_API __attribute__((visibility("default")))
    #endif
#else
    #ifdef _WIN32
        #define NAKI_API __declspec(dllimport)
    #else
        #define NAKI_API
    #endif
#endif

/* 编解码器类型 */
typedef enum {
    NAKI_CODEC_H264 = 0,
    NAKI_CODEC_HEVC = 1,
    NAKI_CODEC_VVC  = 2,
    NAKI_CODEC_AV1  = 3,
    NAKI_CODEC_VP9  = 4,
    NAKI_CODEC_MPEG2 = 5,
    NAKI_CODEC_MPEG4 = 6,
} NakiCodecType;

/* NAL单元结构 */
typedef struct NakiNalUnit {
    const uint8_t *data;
    size_t size;
    int type;
    size_t offset;
    int layer_id;
    int temporal_id;
} NakiNalUnit;

/* 解析器上下文 */
typedef struct NakiParser NakiParser;

/* 回调 */
typedef void (*NakiNalCallback)(const NakiNalUnit *nal, void *userdata);

/* ========== API ========== */

NAKI_API const char* naki_parser_version(void);
NAKI_API uint32_t naki_parser_version_number(void);

NAKI_API NakiParser* naki_parser_create(NakiCodecType codec);
NAKI_API void naki_parser_free(NakiParser *parser);

NAKI_API int naki_parser_parse(NakiParser *parser,
                               const uint8_t *data, size_t size,
                               NakiNalCallback callback, void *userdata);

NAKI_API const char* naki_parser_nal_name(int nal_type, NakiCodecType codec);

NAKI_API int naki_parser_annexb_to_mp4(NakiParser *parser,
                                       const uint8_t *input, size_t input_size,
                                       uint8_t *output, size_t *output_size,
                                       int length_size);

NAKI_API int naki_parser_mp4_to_annexb(NakiParser *parser,
                                       const uint8_t *input, size_t input_size,
                                       uint8_t *output, size_t *output_size,
                                       int length_size);

NAKI_API int naki_parser_find_units(const uint8_t *data, size_t size,
                                    NakiCodecType codec,
                                    NakiNalUnit **nals_out, size_t *count_out);

NAKI_API void naki_parser_free_units(NakiNalUnit *nals);

#ifdef __cplusplus
}
#endif

#endif /* NAKI_PARSER_H */
