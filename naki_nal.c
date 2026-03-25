/**
 * NakiNAL - NAL Analysis Library Implementation
 *
 * 静态链接FFmpeg，只导出NAL工具API
 */

#define NAKI_NAL_BUILD 1
#include "naki_nal.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* FFmpeg headers - 静态链接，不导出 */
#include <libavcodec/avcodec.h>
#include <libavcodec/bsf.h>
#include <libavutil/avutil.h>

/* 版本字符串 */
static const char *version_str = "NakiNAL 1.0.0 (FFmpeg " FFMS_VERSION ")";

/* NAL解析器上下文 */
struct NalParser {
    NakiCodecType codec;
    const AVCodec *av_codec;
    AVCodecParserContext *parser_ctx;
    AVCodecContext *codec_ctx;
    AVBSFContext *bsf_ctx;
};

/* ========== 内部辅助函数 ========== */

/* 查找start code，返回其位置和长度(3或4) */
static const uint8_t* find_start_code(const uint8_t *data, size_t size,
                                      int *start_code_len)
{
    const uint8_t *p = data;
    const uint8_t *end = data + size;

    while (p + 3 <= end) {
        if (p[0] == 0 && p[1] == 0) {
            if (p[2] == 1) {
                *start_code_len = 3;
                return p;
            }
            if (p + 4 <= end && p[2] == 0 && p[3] == 1) {
                *start_code_len = 4;
                return p;
            }
        }
        p++;
    }
    return NULL;
}

/* 获取NAL类型 */
static int get_nal_type(uint8_t first_byte, NakiCodecType codec)
{
    switch (codec) {
    case CODEC_H264:
        return first_byte & 0x1F;
    case CODEC_HEVC:
    case CODEC_VVC:
        return (first_byte >> 1) & 0x3F;
    case CODEC_AV1:
        return first_byte; /* OBU type */
    default:
        return first_byte;
    }
}

/* H.264 NAL类型名称 */
static const char* h264_nal_name(int type)
{
    static const char *names[] = {
        [0]  = "Unspecified",
        [1]  = "Non-IDR Slice",
        [2]  = "Slice Data A",
        [3]  = "Slice Data B",
        [4]  = "Slice Data C",
        [5]  = "IDR Slice",
        [6]  = "SEI",
        [7]  = "SPS",
        [8]  = "PPS",
        [9]  = "AUD",
        [10] = "End of Sequence",
        [11] = "End of Stream",
        [12] = "Filler",
        [13] = "SPS Extension",
        [14] = "Prefix NAL",
        [15] = "Subset SPS",
        [19] = "Slice Extension",
        [20] = "Slice Extension D",
        [21] = "Depth Extension",
    };

    if (type >= 0 && type <= 21 && names[type])
        return names[type];
    if (type >= 22 && type <= 23)
        return "Reserved";
    if (type >= 24 && type <= 31)
        return "Unspecified";
    return "Unknown";
}

/* HEVC NAL类型名称 */
static const char* hevc_nal_name(int type)
{
    static const char *names[] = {
        [0]  = "TRAIL_N",
        [1]  = "TRAIL_R",
        [2]  = "TSA_N",
        [3]  = "TSA_R",
        [4]  = "STSA_N",
        [5]  = "STSA_R",
        [6]  = "RADL_N",
        [7]  = "RADL_R",
        [8]  = "RASL_N",
        [9]  = "RASL_R",
        [16] = "BLA_W_LP",
        [17] = "BLA_W_RADL",
        [18] = "BLA_N_LP",
        [19] = "IDR_W_RADL",
        [20] = "IDR_N_LP",
        [21] = "CRA_NUT",
        [32] = "VPS",
        [33] = "SPS",
        [34] = "PPS",
        [35] = "AUD",
        [36] = "EOS_NUT",
        [37] = "EOB_NUT",
        [38] = "FD_NUT",
        [39] = "PREFIX_SEI",
        [40] = "SUFFIX_SEI",
    };

    if (type >= 0 && type <= 40 && names[type])
        return names[type];
    if (type >= 10 && type <= 15)
        return "RSV_RAP";
    if (type >= 22 && type <= 23)
        return "RSV_IRAP";
    if (type >= 41 && type <= 47)
        return "RSV";
    if (type >= 48)
        return "Unspecified";
    return "Unknown";
}

/* VVC NAL类型名称 */
static const char* vvc_nal_name(int type)
{
    static const char *names[] = {
        [0]  = "TRAIL",
        [1]  = "STSA",
        [2]  = "RADL",
        [3]  = "RASL",
        [4]  = "RSV",
        [5]  = "RSV",
        [6]  = "RSV",
        [7]  = "IDR_W_RADL",
        [8]  = "IDR_N_LP",
        [9]  = "CRA",
        [10] = "GDR",
        [11] = "RSV_IRAP",
        [12] = "OPI",
        [13] = "DCI",
        [14] = "VPS",
        [15] = "SPS",
        [16] = "PPS",
        [17] = "PREFIX_APS",
        [18] = "SUFFIX_APS",
        [19] = "PH",
        [20] = "AUD",
        [21] = "EOS",
        [22] = "EOB",
        [23] = "PREFIX_SEI",
        [24] = "SUFFIX_SEI",
        [25] = "FD",
    };

    if (type >= 0 && type <= 25 && names[type])
        return names[type];
    return "Unknown";
}

/* ========== 公开API实现 ========== */

NAKI_API const char* naki_nal_version(void)
{
    return version_str;
}

NAKI_API uint32_t naki_nal_version_number(void)
{
    return (NAKI_NAL_VERSION_MAJOR << 16) |
           (NAKI_NAL_VERSION_MINOR << 8) |
           NAKI_NAL_VERSION_PATCH;
}

NAKI_API NalParser* naki_nal_parser_create(NakiCodecType codec)
{
    NalParser *parser = calloc(1, sizeof(NalParser));
    if (!parser)
        return NULL;

    parser->codec = codec;

    /* 选择FFmpeg codec ID */
    enum AVCodecID codec_id;
    switch (codec) {
    case CODEC_H264:
        codec_id = AV_CODEC_ID_H264;
        break;
    case CODEC_HEVC:
        codec_id = AV_CODEC_ID_HEVC;
        break;
    case CODEC_VVC:
        codec_id = AV_CODEC_ID_VVC;
        break;
    case CODEC_AV1:
        codec_id = AV_CODEC_ID_AV1;
        break;
    default:
        free(parser);
        return NULL;
    }

    /* 查找解码器 */
    parser->av_codec = avcodec_find_decoder(codec_id);
    if (!parser->av_codec) {
        free(parser);
        return NULL;
    }

    /* 创建解析器上下文 */
    parser->parser_ctx = av_parser_init(codec_id);
    if (!parser->parser_ctx) {
        free(parser);
        return NULL;
    }

    /* 创建解码器上下文 */
    parser->codec_ctx = avcodec_alloc_context3(parser->av_codec);
    if (!parser->codec_ctx) {
        av_parser_close(parser->parser_ctx);
        free(parser);
        return NULL;
    }

    /* 打开解码器 */
    if (avcodec_open2(parser->codec_ctx, parser->av_codec, NULL) < 0) {
        avcodec_free_context(&parser->codec_ctx);
        av_parser_close(parser->parser_ctx);
        free(parser);
        return NULL;
    }

    return parser;
}

NAKI_API void naki_nal_parser_free(NalParser *parser)
{
    if (!parser)
        return;

    if (parser->bsf_ctx)
        av_bsf_free(&parser->bsf_ctx);
    if (parser->codec_ctx)
        avcodec_free_context(&parser->codec_ctx);
    if (parser->parser_ctx)
        av_parser_close(parser->parser_ctx);

    free(parser);
}

NAKI_API int naki_nal_parse(NalParser *parser,
                            const uint8_t *data, size_t size,
                            NalCallback callback, void *userdata)
{
    if (!parser || !data || !callback)
        return -1;

    int count = 0;
    const uint8_t *p = data;
    const uint8_t *end = data + size;
    int start_code_len;

    while (p < end) {
        int sc_len;
        const uint8_t *sc = find_start_code(p, end - p, &sc_len);
        if (!sc)
            break;

        /* 跳过start code */
        const uint8_t *nal_start = sc + sc_len;

        /* 找下一个start code来确定NAL大小 */
        const uint8_t *next_sc = find_start_code(nal_start, end - nal_start, &start_code_len);
        size_t nal_size;
        if (next_sc)
            nal_size = next_sc - nal_start;
        else
            nal_size = end - nal_start;

        if (nal_size > 0) {
            NalUnit nal = {0};
            nal.data = nal_start;
            nal.size = nal_size;
            nal.type = get_nal_type(nal_start[0], parser->codec);
            nal.offset = sc - data;

            /* HEVC/VVC: 解析layer_id和temporal_id */
            if (parser->codec == CODEC_HEVC || parser->codec == CODEC_VVC) {
                if (nal_size >= 2) {
                    nal.nuh_layer_id = (nal_start[0] >> 5) | ((nal_start[1] & 0x01) << 3);
                    nal.nuh_temporal_id = (nal_start[1] >> 5) & 0x07;
                }
            }

            callback(&nal, userdata);
            count++;
        }

        p = nal_start + nal_size;
    }

    return count;
}

NAKI_API const char* naki_nal_type_name(int nal_type, NakiCodecType codec)
{
    switch (codec) {
    case CODEC_H264:
        return h264_nal_name(nal_type);
    case CODEC_HEVC:
        return hevc_nal_name(nal_type);
    case CODEC_VVC:
        return vvc_nal_name(nal_type);
    case CODEC_AV1:
        return "OBU"; /* AV1 OBU */
    default:
        return "Unknown";
    }
}

NAKI_API int naki_nal_annexb_to_mp4(NalParser *parser,
                                    const uint8_t *input, size_t input_size,
                                    uint8_t *output, size_t *output_size,
                                    int length_size)
{
    if (!parser || !input || !output_size)
        return -1;

    /* 计算输出大小 */
    size_t total_size = 0;
    const uint8_t *p = input;
    const uint8_t *end = input + input_size;
    int sc_len;
    size_t nal_count = 0;

    while (p < end) {
        const uint8_t *sc = find_start_code(p, end - p, &sc_len);
        if (!sc)
            break;

        const uint8_t *nal_start = sc + sc_len;
        const uint8_t *next_sc = find_start_code(nal_start, end - nal_start, &sc_len);
        size_t nal_size = next_sc ? (next_sc - nal_start) : (end - nal_start);

        total_size += length_size + nal_size;
        nal_count++;

        p = nal_start + nal_size;
    }

    if (!output) {
        *output_size = total_size;
        return 0;
    }

    if (*output_size < total_size) {
        *output_size = total_size;
        return -2; /* buffer too small */
    }

    /* 转换 */
    uint8_t *out = output;
    p = input;

    while (p < end) {
        const uint8_t *sc = find_start_code(p, end - p, &sc_len);
        if (!sc)
            break;

        const uint8_t *nal_start = sc + sc_len;
        const uint8_t *next_sc = find_start_code(nal_start, end - nal_start, &sc_len);
        size_t nal_size = next_sc ? (next_sc - nal_start) : (end - nal_start);

        /* 写长度 */
        if (length_size == 4) {
            *out++ = (nal_size >> 24) & 0xFF;
            *out++ = (nal_size >> 16) & 0xFF;
            *out++ = (nal_size >> 8) & 0xFF;
            *out++ = nal_size & 0xFF;
        } else if (length_size == 2) {
            *out++ = (nal_size >> 8) & 0xFF;
            *out++ = nal_size & 0xFF;
        } else {
            *out++ = nal_size & 0xFF;
        }

        /* 写NAL数据 */
        memcpy(out, nal_start, nal_size);
        out += nal_size;

        p = nal_start + nal_size;
    }

    *output_size = out - output;
    return 0;
}

NAKI_API int naki_nal_mp4_to_annexb(NalParser *parser,
                                    const uint8_t *input, size_t input_size,
                                    uint8_t *output, size_t *output_size,
                                    int length_size)
{
    if (!parser || !input || !output_size)
        return -1;

    static const uint8_t start_code[4] = {0, 0, 0, 1};

    /* 计算输出大小 */
    size_t total_size = 0;
    const uint8_t *p = input;
    const uint8_t *end = input + input_size;

    while (p + length_size <= end) {
        size_t nal_size = 0;
        for (int i = 0; i < length_size; i++) {
            nal_size = (nal_size << 8) | p[i];
        }

        if (p + length_size + nal_size > end)
            break;

        total_size += 4 + nal_size; /* 4字节start code + NAL数据 */
        p += length_size + nal_size;
    }

    if (!output) {
        *output_size = total_size;
        return 0;
    }

    if (*output_size < total_size) {
        *output_size = total_size;
        return -2;
    }

    /* 转换 */
    uint8_t *out = output;
    p = input;

    while (p + length_size <= end) {
        size_t nal_size = 0;
        for (int i = 0; i < length_size; i++) {
            nal_size = (nal_size << 8) | p[i];
        }

        if (p + length_size + nal_size > end)
            break;

        /* 写start code */
        memcpy(out, start_code, 4);
        out += 4;

        /* 写NAL数据 */
        memcpy(out, p + length_size, nal_size);
        out += nal_size;

        p += length_size + nal_size;
    }

    *output_size = out - output;
    return 0;
}

NAKI_API int naki_nal_extract_paramsets(NalParser *parser,
                                        const uint8_t *data, size_t size,
                                        uint8_t **vps_out, size_t *vps_size,
                                        uint8_t **sps_out, size_t *sps_size,
                                        uint8_t **pps_out, size_t *pps_size)
{
    if (!parser || !data)
        return -1;

    int count = 0;

    if (vps_out) *vps_out = NULL;
    if (vps_size) *vps_size = 0;
    if (sps_out) *sps_out = NULL;
    if (sps_size) *sps_size = 0;
    if (pps_out) *pps_out = NULL;
    if (pps_size) *pps_size = 0;

    const uint8_t *p = data;
    const uint8_t *end = data + size;
    int sc_len;

    while (p < end) {
        const uint8_t *sc = find_start_code(p, end - p, &sc_len);
        if (!sc)
            break;

        const uint8_t *nal_start = sc + sc_len;
        const uint8_t *next_sc = find_start_code(nal_start, end - nal_start, &sc_len);
        size_t nal_size = next_sc ? (next_sc - nal_start) : (end - nal_start);

        int nal_type = get_nal_type(nal_start[0], parser->codec);
        int is_paramset = 0;

        switch (parser->codec) {
        case CODEC_H264:
            if (nal_type == NAL_H264_SPS && sps_out) {
                *sps_out = malloc(nal_size);
                if (*sps_out) {
                    memcpy(*sps_out, nal_start, nal_size);
                    *sps_size = nal_size;
                    is_paramset = 1;
                }
            } else if (nal_type == NAL_H264_PPS && pps_out) {
                *pps_out = malloc(nal_size);
                if (*pps_out) {
                    memcpy(*pps_out, nal_start, nal_size);
                    *pps_size = nal_size;
                    is_paramset = 1;
                }
            }
            break;

        case CODEC_HEVC:
        case CODEC_VVC:
            if (nal_type == NAL_HEVC_VPS && vps_out) {
                *vps_out = malloc(nal_size);
                if (*vps_out) {
                    memcpy(*vps_out, nal_start, nal_size);
                    *vps_size = nal_size;
                    is_paramset = 1;
                }
            } else if (nal_type == NAL_HEVC_SPS && sps_out) {
                *sps_out = malloc(nal_size);
                if (*sps_out) {
                    memcpy(*sps_out, nal_start, nal_size);
                    *sps_size = nal_size;
                    is_paramset = 1;
                }
            } else if (nal_type == NAL_HEVC_PPS && pps_out) {
                *pps_out = malloc(nal_size);
                if (*pps_out) {
                    memcpy(*pps_out, nal_start, nal_size);
                    *pps_size = nal_size;
                    is_paramset = 1;
                }
            }
            break;

        default:
            break;
        }

        if (is_paramset)
            count++;

        p = nal_start + nal_size;
    }

    return count;
}

NAKI_API void naki_nal_free_buffers(uint8_t *vps, uint8_t *sps, uint8_t *pps)
{
    free(vps);
    free(sps);
    free(pps);
}

/* 简化API实现 */

typedef struct {
    NalUnit *nals;
    size_t count;
    size_t capacity;
} NalArray;

static void collect_nal(const NalUnit *nal, void *userdata)
{
    NalArray *arr = (NalArray*)userdata;

    if (arr->count >= arr->capacity) {
        size_t new_cap = arr->capacity * 2 + 16;
        NalUnit *new_nals = realloc(arr->nals, new_cap * sizeof(NalUnit));
        if (!new_nals)
            return;
        arr->nals = new_nals;
        arr->capacity = new_cap;
    }

    /* 复制数据（只复制元信息，不复制NAL内容） */
    arr->nals[arr->count] = *nal;
    arr->count++;
}

NAKI_API int naki_nal_find_units(const uint8_t *data, size_t size,
                                 NakiCodecType codec,
                                 NalUnit **nals_out, size_t *count_out)
{
    if (!data || !nals_out || !count_out)
        return -1;

    NalParser *parser = naki_nal_parser_create(codec);
    if (!parser)
        return -2;

    NalArray arr = {0};
    int result = naki_nal_parse(parser, data, size, collect_nal, &arr);

    naki_nal_parser_free(parser);

    if (result >= 0) {
        *nals_out = arr.nals;
        *count_out = arr.count;
    }

    return result;
}

NAKI_API void naki_nal_free_units(NalUnit *nals)
{
    free(nals);
}
