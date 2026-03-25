/**
 * NakiParser - Video Stream Parser Library Implementation
 */

#define NAKI_PARSER_BUILD 1
#include "naki_parser.h"

#include <stdlib.h>
#include <string.h>

/* 版本 */
static const char *version_str = "NakiParser 1.0.0";

/* 解析器上下文 */
struct NakiParser {
    NakiCodecType codec;
};

/* 查找 start code */
static const uint8_t* find_start_code(const uint8_t *data, size_t size, int *len)
{
    for (size_t i = 0; i + 3 <= size; i++) {
        if (data[i] == 0 && data[i+1] == 0) {
            if (data[i+2] == 1) { *len = 3; return data + i; }
            if (i + 4 <= size && data[i+2] == 0 && data[i+3] == 1) { *len = 4; return data + i; }
        }
    }
    return NULL;
}

/* 获取 NAL 类型 */
static int get_nal_type(uint8_t first_byte, NakiCodecType codec)
{
    switch (codec) {
    case NAKI_CODEC_H264: return first_byte & 0x1F;
    case NAKI_CODEC_HEVC:
    case NAKI_CODEC_VVC:  return (first_byte >> 1) & 0x3F;
    default: return first_byte;
    }
}

/* NAL 类型名称 */
static const char* get_nal_name(int type, NakiCodecType codec)
{
    if (codec == NAKI_CODEC_H264) {
        static const char *h264[] = {
            [0]="Unspec", [1]="Slice", [5]="IDR", [6]="SEI", [7]="SPS", [8]="PPS", [9]="AUD"
        };
        return (type >= 0 && type <= 9 && h264[type]) ? h264[type] : "Other";
    }
    if (codec == NAKI_CODEC_HEVC || codec == NAKI_CODEC_VVC) {
        static const char *hevc[] = {
            [19]="IDR", [20]="IDR", [21]="CRA", [32]="VPS", [33]="SPS", [34]="PPS", [35]="AUD"
        };
        return (type >= 0 && type <= 40 && hevc[type]) ? hevc[type] : "Other";
    }
    return "Unknown";
}

/* ========== API ========== */

NAKI_API const char* naki_parser_version(void)
{
    return version_str;
}

NAKI_API uint32_t naki_parser_version_number(void)
{
    return (NAKI_PARSER_VERSION_MAJOR << 16) | (NAKI_PARSER_VERSION_MINOR << 8) | NAKI_PARSER_VERSION_PATCH;
}

NAKI_API NakiParser* naki_parser_create(NakiCodecType codec)
{
    NakiParser *p = calloc(1, sizeof(*p));
    if (p) p->codec = codec;
    return p;
}

NAKI_API void naki_parser_free(NakiParser *parser)
{
    free(parser);
}

NAKI_API int naki_parser_parse(NakiParser *parser, const uint8_t *data, size_t size,
                               NakiNalCallback callback, void *userdata)
{
    if (!parser || !data || !callback) return -1;

    int count = 0;
    const uint8_t *p = data, *end = data + size;
    int sc_len;

    while (p < end) {
        const uint8_t *sc = find_start_code(p, end - p, &sc_len);
        if (!sc) break;

        const uint8_t *nal = sc + sc_len;
        int next_len;
        const uint8_t *next = find_start_code(nal, end - nal, &next_len);
        size_t nal_size = next ? (next - nal) : (end - nal);

        if (nal_size > 0) {
            NakiNalUnit unit = {
                .data = nal,
                .size = nal_size,
                .type = get_nal_type(nal[0], parser->codec),
                .offset = sc - data,
            };
            callback(&unit, userdata);
            count++;
        }
        p = nal + nal_size;
    }
    return count;
}

/* 导出的 NAL 名称函数 */
NAKI_API const char* naki_parser_nal_name(int nal_type, NakiCodecType codec)
{
    return get_nal_name(nal_type, codec);
}

NAKI_API int naki_parser_find_units(const uint8_t *data, size_t size, NakiCodecType codec,
                                    NakiNalUnit **nals_out, size_t *count_out)
{
    if (!data || !nals_out || !count_out) return -1;

    NakiParser *parser = naki_parser_create(codec);
    if (!parser) return -2;

    /* 简单实现：最多256个NAL */
    NakiNalUnit *nals = malloc(256 * sizeof(*nals));
    size_t count = 0;

    const uint8_t *p = data, *end = data + size;
    int sc_len;

    while (p < end && count < 256) {
        const uint8_t *sc = find_start_code(p, end - p, &sc_len);
        if (!sc) break;

        const uint8_t *nal = sc + sc_len;
        int next_len;
        const uint8_t *next = find_start_code(nal, end - nal, &next_len);
        size_t nal_size = next ? (next - nal) : (end - nal);

        nals[count++] = (NakiNalUnit){
            .data = nal,
            .size = nal_size,
            .type = get_nal_type(nal[0], codec),
            .offset = sc - data,
        };
        p = nal + nal_size;
    }

    naki_parser_free(parser);
    *nals_out = nals;
    *count_out = count;
    return 0;
}

NAKI_API void naki_parser_free_units(NakiNalUnit *nals)
{
    free(nals);
}

/* 格式转换简化实现 */
NAKI_API int naki_parser_annexb_to_mp4(NakiParser *parser,
                                       const uint8_t *input, size_t input_size,
                                       uint8_t *output, size_t *output_size,
                                       int length_size)
{
    /* TODO */
    (void)parser; (void)input; (void)input_size; (void)output; (void)output_size; (void)length_size;
    return -1;
}

NAKI_API int naki_parser_mp4_to_annexb(NakiParser *parser,
                                       const uint8_t *input, size_t input_size,
                                       uint8_t *output, size_t *output_size,
                                       int length_size)
{
    /* TODO */
    (void)parser; (void)input; (void)input_size; (void)output; (void)output_size; (void)length_size;
    return -1;
}
