/**
 * NakiParser Test
 */

#include <stdio.h>
#include <stdlib.h>
#include "naki_parser.h"

static const uint8_t test_h264[] = {
    0x00, 0x00, 0x00, 0x01, 0x67, 0x42, 0x00, 0x1e, 0x89, 0x8b, 0x60, 0x50,
    0x00, 0x00, 0x00, 0x01, 0x68, 0xce, 0x3c, 0x80,
    0x00, 0x00, 0x00, 0x01, 0x65, 0x88, 0x80, 0x10, 0x00, 0x00, 0x03, 0x00,
};

static int g_count = 0;

static void on_nal(const NakiNalUnit *nal, void *userdata)
{
    (void)userdata;
    const char *name = naki_parser_nal_name(nal->type, NAKI_CODEC_H264);
    printf("  [%d] Type %2d (%s): %zu bytes @ %zu\n",
           g_count++, nal->type, name, nal->size, nal->offset);
}

int main(void)
{
    printf("NakiParser Test\n");
    printf("===============\n\n");

    printf("Version: %s\n\n", naki_parser_version());

    /* 回调方式 */
    NakiParser *parser = naki_parser_create(NAKI_CODEC_H264);
    if (!parser) {
        fprintf(stderr, "Failed to create parser\n");
        return 1;
    }

    printf("Parse with callback:\n");
    int count = naki_parser_parse(parser, test_h264, sizeof(test_h264), on_nal, NULL);
    printf("Found %d NAL units\n\n", count);

    naki_parser_free(parser);

    /* 简化 API */
    printf("Parse with find_units:\n");
    NakiNalUnit *nals = NULL;
    size_t nal_count = 0;
    naki_parser_find_units(test_h264, sizeof(test_h264), NAKI_CODEC_H264, &nals, &nal_count);
    for (size_t i = 0; i < nal_count; i++) {
        printf("  NAL %zu: type=%d size=%zu\n", i, nals[i].type, nals[i].size);
    }
    naki_parser_free_units(nals);

    printf("\nOK\n");
    return 0;
}
