#include <assert.h>
#include <stdio.h>
#include "protocol.h"
int main(void){assert(ql_crc32((const unsigned char*)"123456789",9)==0xcbf43926);assert(ql_crc32((const unsigned char*)"",0)==0);for(unsigned a=0;a<16384;a++)assert(ql_parity(ql_read_command((uint16_t)a))==0);assert(ql_response_ok(0));assert(!ql_response_ok(1));assert(!ql_response_ok(0xc000));uint8_t positive[]={0x3e,0x80,0x00},negative[]={0xc1,0x80,0x00};assert(ql_axis20(positive)==256000);assert(ql_axis20(negative)==-256000);assert(ql_diagnostic_ok(0x8100));assert(!ql_diagnostic_ok(0));puts("CRC, 16384 command parities, response errors, signed 20-bit acceleration and diagnostic checks passed");}
