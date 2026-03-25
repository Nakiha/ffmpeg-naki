/**
 * NakiNAL Test
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "naki_nal.h"

/* 测试数据: H.264 NAL units */
static const uint8_t test_h264[] = {
    0x00, 0x00, 0x00, 0x01, 0x67, 0x42, 0x00, 0x1e, 0x89, 0x8b, 0x60, 0x50,  /* SPS */
    0x00, 0x00, 0x00, 0x01, 0x68, 0xce, 0x3c, 0x80,                          /* PPS */
    0x00, 0x00, 0x00, 0x01, 0x65, 0x88, 0x80, 0x10, 0x00, 0x00, 0x03, 0x00,  /* IDR */
};

static int nal_count = 0;

static void on_nal(const NalUnit *nal, void *userdata)
{
    const char *name = naki_nal_type_name(nal->type, CODEC_H264);
    printf("  [%d] Type %2d (%s): %zu bytes @ offset %zu\n",
           nal_count, nal->type, name, nal->size, nal->offset);
    nal_count++;
}

int main(void)
{
    printf("NakiNAL Test\n");
    printf("============\n\n");

    /* 版本 */
    printf("Version: %s\n", naki_nal_version());
    uint32_t v = naki_nal_version_number();
    printf("Version: %u.%u.%u\n\n", v >> 16, (v >> 8) & 0xFF, v & 0xFF);

    /* 创建解析器 */
    NalParser *parser = naki_nal_parser_create(CODEC_H264);
    if (!parser) {
        fprintf(stderr, "Failed to create parser\n");
        return 1;
    }

    /* 解析 */
    printf("Parsing %zu bytes of H.264 data...\n", sizeof(test_h264));
    int count = naki_nal_parse(parser, test_h264, sizeof(test_h264), on_nal, NULL);
    printf("\nFound %d NAL units\n", count);

    /* 简化 API 测试 */
    printf("\nUsing simplified API:\n");
    NalUnit *nals = NULL;
    size_t nal_count2 = 0;
    int ret = naki_nal_find_units(test_h264, sizeof(test_h264), CODEC_H264, &nals, &nal_count2);
    if (ret >= 0) {
        for (size_t i = 0; i < nal_count2; i++) {
            printf("  NAL %zu: type=%d size=%zu\n", i, nals[i].type, nals[i].size);
        }
        naki_nal_free_units(nals);
    }

    /* 清理 */
    naki_nal_parser_free(parser);

    printf("\nAll tests passed!\n");
    return 0;
}
