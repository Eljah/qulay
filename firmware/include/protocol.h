#ifndef QULAY_PROTOCOL_H
#define QULAY_PROTOCOL_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
static inline uint32_t ql_crc32(const unsigned char *data,size_t len){uint32_t c=0xffffffffu;for(size_t i=0;i<len;i++){c^=data[i];for(unsigned k=0;k<8;k++)c=(c>>1)^((0u-(c&1u))&0xedb88320u);}return ~c;}
static inline unsigned ql_parity(uint16_t x){x^=x>>8;x^=x>>4;x^=x>>2;x^=x>>1;return x&1u;}
static inline uint16_t ql_read_command(uint16_t address){uint16_t w=0x4000u|(address&0x3fffu);return w|(ql_parity(w)<<15);}
static inline bool ql_response_ok(uint16_t w){return ql_parity(w)==0 && !(w&0x4000u);}
static inline bool ql_diagnostic_ok(uint16_t w){return ql_response_ok(w)&&(w&0x0100u)&&!(w&0x0e00u);}
static inline int32_t ql_axis20(const uint8_t *p){uint32_t v=((uint32_t)p[0]<<12)|((uint32_t)p[1]<<4)|(p[2]>>4);return v&0x80000u?(int32_t)v-0x100000:(int32_t)v;}
#endif
