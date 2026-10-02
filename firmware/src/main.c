/* QL-01 prototype acquisition; real contact detection and independent datum are NOT implemented. */
#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/sync.h"
#include "protocol.h"
static const uint cs_bank[4]={5,6,7,8};
static const unsigned bank_size[4]={8,8,8,7};
static volatile int64_t odo=0;
static volatile unsigned old_ab=0;
static void odo_irq(uint gpio,uint32_t events){
 (void)gpio;(void)events;static const int8_t table[16]={0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0};
 unsigned ab=(gpio_get(0)?2:0)|(gpio_get(1)?1:0);odo+=table[(old_ab<<2)|ab];old_ab=ab;
}
static void chain_transfer(unsigned bank,uint16_t word,uint16_t *rx){
 uint16_t tx[8];for(unsigned i=0;i<bank_size[bank];i++)tx[i]=word;
 gpio_put(cs_bank[bank],0);busy_wait_us_32(1);spi_write16_read16_blocking(spi0,tx,rx,bank_size[bank]);busy_wait_us_32(1);gpio_put(cs_bank[bank],1);busy_wait_us_32(1);
}
static void chain_read(unsigned bank,uint16_t address,uint16_t *words){
 uint16_t trash[8],rx[8];chain_transfer(bank,ql_read_command(address),trash);chain_transfer(bank,0,rx);
 for(unsigned i=0;i<bank_size[bank];i++)words[i]=rx[bank_size[bank]-1-i];
}
static void ad_read(uint8_t address,uint8_t *bytes,size_t n){uint8_t command=(address<<1)|1;gpio_put(13,0);spi_write_blocking(spi1,&command,1);spi_read_blocking(spi1,0,bytes,n);gpio_put(13,1);}
static void ad_write(uint8_t address,uint8_t value){uint8_t tx[2]={address<<1,value};gpio_put(13,0);spi_write_blocking(spi1,tx,2);gpio_put(13,1);}
static bool ad_init(void){uint8_t id[3];ad_read(0,id,3);if(id[0]!=0xad||id[1]!=0x1d||id[2]!=0xed)return false;
 ad_write(0x2d,1);ad_write(0x28,4);/* 250 Hz ODR, HPF off; group delay must be calibrated for dynamic work. */
 ad_write(0x2c,0x81);ad_write(0x2d,0);sleep_ms(50);return true;
}
int main(void){
 stdio_init_all();
 for(unsigned bank=0;bank<4;bank++){gpio_init(cs_bank[bank]);gpio_set_dir(cs_bank[bank],GPIO_OUT);gpio_put(cs_bank[bank],1);}
 spi_init(spi0,1000000);spi_set_format(spi0,16,SPI_CPOL_0,SPI_CPHA_1,SPI_MSB_FIRST);
 gpio_set_function(2,GPIO_FUNC_SPI);gpio_set_function(3,GPIO_FUNC_SPI);gpio_set_function(4,GPIO_FUNC_SPI);
 gpio_init(13);gpio_set_dir(13,GPIO_OUT);gpio_put(13,1);
 spi_init(spi1,1000000);spi_set_format(spi1,8,SPI_CPOL_0,SPI_CPHA_0,SPI_MSB_FIRST);
 gpio_set_function(10,GPIO_FUNC_SPI);gpio_set_function(11,GPIO_FUNC_SPI);gpio_set_function(12,GPIO_FUNC_SPI);
 for(uint p=0;p<2;p++){gpio_init(p);gpio_set_dir(p,GPIO_IN);gpio_pull_up(p);}
 old_ab=(gpio_get(0)?2:0)|(gpio_get(1)?1:0);
 gpio_set_irq_enabled_with_callback(0,GPIO_IRQ_EDGE_RISE|GPIO_IRQ_EDGE_FALL,true,&odo_irq);gpio_set_irq_enabled(1,GPIO_IRQ_EDGE_RISE|GPIO_IRQ_EDGE_FALL,true);
 gpio_init(25);gpio_set_dir(25,GPIO_OUT);sleep_ms(100);bool ad_present=ad_init();
 uint64_t sequence=0;absolute_time_t due=get_absolute_time();
 while(true){
  due=delayed_by_us(due,10000);uint64_t time=time_us_64();uint32_t save=save_and_disable_interrupts();int64_t odometry=odo;restore_interrupts(save);
  uint16_t angle[31]={0};uint32_t valid=0;unsigned offset=0;
  for(unsigned b=0;b<4;b++){
   uint16_t diag[8],raw[8];chain_read(b,0x3ffd,diag);chain_read(b,0x3fff,raw);bool needs_clear=false;
   for(unsigned k=0;k<bank_size[b];k++){angle[offset+k]=raw[k]&0x3fff;if(ql_response_ok(raw[k])&&ql_diagnostic_ok(diag[k]))valid|=1u<<(offset+k);else needs_clear=true;}
   if(needs_clear){uint16_t discarded[8];chain_read(b,1,discarded);}offset+=bank_size[b];
  }
  int32_t ax=0,ay=0,az=0;
  if(ad_present){uint8_t status;ad_read(4,&status,1);if((status&1)&&!(status&0x10)){uint8_t raw[9];ad_read(8,raw,9);ax=ql_axis20(raw);ay=ql_axis20(raw+3);az=ql_axis20(raw+6);}}
  char line[768];int n=snprintf(line,sizeof line,"Q1,%" PRIu64 ",%" PRIu64 ",%" PRId64 ",%" PRId32 ",%" PRId32 ",%" PRId32 ",%08" PRIx32,sequence,time,odometry,ax,ay,az,valid);
  for(unsigned j=0;j<31&&n>0&&(size_t)n<sizeof line;j++)n+=snprintf(line+n,sizeof line-(size_t)n,",%u",angle[j]);
  if(n>0&&(size_t)n<sizeof line)printf("%s*%08" PRIx32 "\n",line,ql_crc32((const unsigned char*)line,(size_t)n));
  gpio_put(25,(sequence/50)%2);sequence++;
  /* USB backpressure can delay a frame. Actual timestamps, not idealized time, are transmitted. */
  if(absolute_time_diff_us(get_absolute_time(),due)<0)due=get_absolute_time();sleep_until(due);
 }
}
