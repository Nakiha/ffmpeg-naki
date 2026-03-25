/**
 * NakiNAL - NAL Analysis Library
 *
 * 静态链接FFmpeg，只导出NAL分析相关API
 * 避免与系统其他FFmpeg库符号冲突
 */

#ifndef NAKI_NAL_H
#define NAKI_NAL_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 版本信息 */
#define NAKI_NAL_VERSION_MAJOR 1
#define NAKI_NAL_VERSION_MINOR 0
#define NAKI_NAL_VERSION_PATCH 0

/* 导出宏 - 只在编译库时导出 */
#ifdef NAKI_NAL_BUILD
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

/* NAL单元类型定义 */
typedef enum {
    /* H.264 NAL types */
    NAL_H264_SLICE      = 1,
    NAL_H264_DPA        = 2,
    NAL_H264_DPB        = 3,
    NAL_H264_DPC        = 4,
    NAL_H264_IDR_SLICE  = 5,
    NAL_H264_SEI        = 6,
    NAL_H264_SPS        = 7,
    NAL_H264_PPS        = 8,
    NAL_H264_AUD        = 9,
    NAL_H264_EOSEQ      = 10,
    NAL_H264_EOSTREAM   = 11,
    NAL_H264_FILL       = 12,

    /* HEVC NAL types */
    NAL_HEVC_TRAIL_N    = 0,
    NAL_HEVC_TRAIL_R    = 1,
    NAL_HEVC_TSA_N      = 2,
    NAL_HEVC_TSA_R      = 3,
    NAL_HEVC_STSA_N     = 4,
    NAL_HEVC_STSA_R     = 5,
    NAL_HEVC_RADL_N     = 6,
    NAL_HEVC_RADL_R     = 7,
    NAL_HEVC_RASL_N     = 8,
    NAL_HEVC_RASL_R     = 9,
    NAL_HEVC_BLA_W_LP   = 16,
    NAL_HEVC_BLA_W_RADL = 17,
    NAL_HEVC_BLA_N_LP   = 18,
    NAL_HEVC_IDR_W_RADL = 19,
    NAL_HEVC_IDR_N_LP   = 20,
    NAL_HEVC_CRA_NUT    = 21,
    NAL_HEVC_VPS        = 32,
    NAL_HEVC_SPS        = 33,
    NAL_HEVC_PPS        = 34,
    NAL_HEVC_AUD        = 35,
    NAL_HEVC_EOS_NUT    = 36,
    NAL_HEVC_EOB_NUT    = 37,
    NAL_HEVC_FD_NUT     = 38,
    NAL_HEVC_PREFIX_SEI = 39,
    NAL_HEVC_SUFFIX_SEI = 40,

    /* VVC NAL types */
    NAL_VVC_OPI         = 12,
    NAL_VVC_DCI         = 13,
    NAL_VVC_VPS         = 14,
    NAL_VVC_SPS         = 15,
    NAL_VVC_PPS         = 16,
    NAL_VVC_PREFIX_APS  = 17,
    NAL_VVC_SUFFIX_APS  = 18,
    NAL_VVC_PH          = 19,
    NAL_VVC_AUD         = 20,
    NAL_VVC_EOS         = 21,
    NAL_VVC_EOB         = 22,
    NAL_VVC_PREFIX_SEI  = 23,
    NAL_VVC_SUFFIX_SEI  = 24,
    NAL_VVC_IDR_W_RADL  = 7,
    NAL_VVC_IDR_N_LP    = 8,
    NAL_VVC_CRA         = 9,
    NAL_VVC_GDR         = 10,
    NAL_VVC_RSV_IRAP_11 = 11,
} NalUnitType;

/* 编解码器类型 */
typedef enum {
    CODEC_H264 = 0,
    CODEC_HEVC = 1,
    CODEC_VVC  = 2,
    CODEC_AV1  = 3,
} NakiCodecType;

/* NAL单元结构 */
typedef struct NalUnit {
    const uint8_t *data;      /* NAL单元数据（不含start code） */
    size_t size;              /* NAL单元大小 */
    int type;                 /* NAL类型 */
    size_t offset;            /* 在原始数据中的偏移 */
    int nuh_layer_id;         /* HEVC/VVC: layer id */
    int nuh_temporal_id;      /* HEVC/VVC: temporal id */
} NalUnit;

/* NAL解析器上下文 */
typedef struct NalParser NalParser;

/* 回调函数类型 */
typedef void (*NalCallback)(const NalUnit *nal, void *userdata);

/* ========== API 函数 ========== */

/**
 * 获取版本字符串
 */
NAKI_API const char* naki_nal_version(void);

/**
 * 获取版本号
 */
NAKI_API uint32_t naki_nal_version_number(void);

/**
 * 创建NAL解析器
 */
NAKI_API NalParser* naki_nal_parser_create(NakiCodecType codec);

/**
 * 销毁NAL解析器
 */
NAKI_API void naki_nal_parser_free(NalParser *parser);

/**
 * 解析数据中的NAL单元
 * @param parser 解析器
 * @param data 输入数据
 * @param size 数据大小
 * @param callback 回调函数，每个NAL单元调用一次
 * @param userdata 用户数据，传递给回调
 * @return 找到的NAL单元数量，负数表示错误
 */
NAKI_API int naki_nal_parse(NalParser *parser,
                            const uint8_t *data, size_t size,
                            NalCallback callback, void *userdata);

/**
 * 获取NAL类型名称
 */
NAKI_API const char* naki_nal_type_name(int nal_type, NakiCodecType codec);

/**
 * 将Annex B格式转换为MP4格式（length-prefixed）
 * @param parser 解析器
 * @param input 输入数据（Annex B格式）
 * @param input_size 输入大小
 * @param output 输出缓冲区（可以为NULL，只返回所需大小）
 * @param output_size 输入时为缓冲区大小，输出时为实际大小
 * @param length_size 长度字段大小（1/2/4字节）
 * @return 0成功，负数错误
 */
NAKI_API int naki_nal_annexb_to_mp4(NalParser *parser,
                                    const uint8_t *input, size_t input_size,
                                    uint8_t *output, size_t *output_size,
                                    int length_size);

/**
 * 将MP4格式转换为Annex B格式
 */
NAKI_API int naki_nal_mp4_to_annexb(NalParser *parser,
                                    const uint8_t *input, size_t input_size,
                                    uint8_t *output, size_t *output_size,
                                    int length_size);

/**
 * 提取SPS/PPS/VPS等参数集
 * @param parser 解析器
 * @param data 输入数据
 * @param size 数据大小
 * @param vps_out VPS输出（HEVC/VVC）
 * @param vps_size VPS大小
 * @param sps_out SPS输出
 * @param sps_size SPS大小
 * @param pps_out PPS输出
 * @param pps_size PPS大小
 * @return 找到的参数集数量
 */
NAKI_API int naki_nal_extract_paramsets(NalParser *parser,
                                        const uint8_t *data, size_t size,
                                        uint8_t **vps_out, size_t *vps_size,
                                        uint8_t **sps_out, size_t *sps_size,
                                        uint8_t **pps_out, size_t *pps_size);

/**
 * 释放extract_paramsets分配的内存
 */
NAKI_API void naki_nal_free_buffers(uint8_t *vps, uint8_t *sps, uint8_t *pps);

/* ========== 简化API（无需解析器上下文） ========== */

/**
 * 快速查找NAL单元（只查找，不解析）
 * @param data 输入数据
 * @param size 数据大小
 * @param codec 编解码类型
 * @param nals_out 输出NAL数组（需要调用者释放）
 * @param count_out 输出NAL数量
 * @return 0成功
 */
NAKI_API int naki_nal_find_units(const uint8_t *data, size_t size,
                                 NakiCodecType codec,
                                 NalUnit **nals_out, size_t *count_out);

/**
 * 释放find_units分配的NAL数组
 */
NAKI_API void naki_nal_free_units(NalUnit *nals);

#ifdef __cplusplus
}
#endif

#endif /* NAKI_NAL_H */
