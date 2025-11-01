# Register Map Documentation

## Address Space Overview

The user project implements 2 UART peripherals with the following address map:

| Peripheral | Base Address | Address Range | Size |
|------------|--------------|---------------|------|
| UART0 | 0x3000_0000 | 0x3000_0000 - 0x3000_FFFF | 64 KB |
| UART1 | 0x3001_0000 | 0x3001_0000 - 0x3001_FFFF | 64 KB |

## Address Decoding

- **Decode bits**: `wbs_adr_i[19:16]`
- **UART0 selection**: `wbs_adr_i[19:16] == 4'b0000`
- **UART1 selection**: `wbs_adr_i[19:16] == 4'b0001`

## UART Register Map (CF_UART_WB)

Both UART0 and UART1 use the CF_UART IP with identical register maps.

### Register Summary

| Register Name | Offset | Reset Value | Access | Description |
|--------------|--------|-------------|--------|-------------|
| RXDATA | 0x0000 | 0x00000000 | R | RX Data register; interface to Receive FIFO |
| TXDATA | 0x0004 | 0x00000000 | W | TX Data register; interface to Transmit FIFO |
| PR | 0x0008 | 0x00000000 | W | Prescaler register for baud rate |
| CTRL | 0x000C | 0x00000000 | W | UART Control Register |
| CFG | 0x0010 | 0x00003F08 | W | UART Configuration Register |
| MATCH | 0x001C | 0x00000000 | W | Match Register |
| RX_FIFO_LEVEL | 0xFE00 | 0x00000000 | R | RX FIFO Level Register |
| RX_FIFO_THRESHOLD | 0xFE04 | 0x00000000 | W | RX FIFO Level Threshold Register |
| RX_FIFO_FLUSH | 0xFE08 | 0x00000000 | W | RX FIFO Flush Register |
| TX_FIFO_LEVEL | 0xFE10 | 0x00000000 | R | TX FIFO Level Register |
| TX_FIFO_THRESHOLD | 0xFE14 | 0x00000000 | W | TX FIFO Level Threshold Register |
| TX_FIFO_FLUSH | 0xFE18 | 0x00000000 | W | TX FIFO Flush Register |
| IM | 0xFF00 | 0x00000000 | W | Interrupt Mask Register |
| RIS | 0xFF08 | 0x00000000 | R | Raw Interrupt Status |
| MIS | 0xFF04 | 0x00000000 | R | Masked Interrupt Status |
| IC | 0xFF0C | 0x00000000 | W | Interrupt Clear Register (W1C) |
| GCLK | 0xFF10 | 0x00000000 | W | Gated clock enable (NOTE: Not used in Caravel - clock gating disabled) |

### Register Details

#### RXDATA Register (Offset: 0x0000, Read-Only)
RX Data register; the interface to the Receive FIFO.
- **Bits [8:0]**: RXDATA - Received data (9 bits max)
- **Bits [31:9]**: Reserved

#### TXDATA Register (Offset: 0x0004, Write-Only)
TX Data register; the interface to the Transmit FIFO.
- **Bits [8:0]**: TXDATA - Data to transmit (9 bits max)
- **Bits [31:9]**: Reserved

#### PR Register (Offset: 0x0008, Write-Only)
Prescaler register; used to determine baud rate.
- **Formula**: `baud_rate = clock_freq / ((PR+1) * SC)`
- **SC**: Samples per bit (default: 8)
- **Bits [15:0]**: PR - Prescaler value
- **Bits [31:16]**: Reserved

#### CTRL Register (Offset: 0x000C, Write-Only)
UART Control Register
- **Bit 0**: EN - UART Enable
- **Bit 1**: TX_EN - Transmitter Enable
- **Bit 2**: RX_EN - Receiver Enable
- **Bit 3**: LOOPBACK - Loopback mode enable
- **Bits [31:4]**: Reserved

#### CFG Register (Offset: 0x0010, Write-Only)
UART Configuration Register
- **Bits [3:0]**: DATA_SIZE - Data bits (5-9 bits)
- **Bit 4**: STOP_BITS - Stop bits count (0: 1 bit, 1: 2 bits)
- **Bits [6:5]**: PARITY_TYPE - Parity (00: None, 01: Odd, 10: Even, 11: Stick)
- **Bit 7**: GLITCH_FILTER_EN - Enable glitch filter on RX
- **Bits [13:8]**: TIMEOUT_BITS - Receiver timeout in bit periods
- **Bits [31:14]**: Reserved

#### MATCH Register (Offset: 0x001C, Write-Only)
Match Register for received data detection
- **Bits [8:0]**: MATCH - Match value
- **Bits [31:9]**: Reserved

#### FIFO Registers
- **RX_FIFO_LEVEL**: Current RX FIFO level (read-only)
- **RX_FIFO_THRESHOLD**: RX FIFO threshold for interrupt
- **RX_FIFO_FLUSH**: Write 1 to flush RX FIFO
- **TX_FIFO_LEVEL**: Current TX FIFO level (read-only)
- **TX_FIFO_THRESHOLD**: TX FIFO threshold for interrupt
- **TX_FIFO_FLUSH**: Write 1 to flush TX FIFO

#### Interrupt Registers

**Interrupt Flags** (bit positions in IM, RIS, MIS, IC):
| Bit | Flag | Description |
|-----|------|-------------|
| 0 | TXE | TX FIFO Empty |
| 1 | RXF | RX FIFO Full |
| 2 | TXB | TX FIFO Below Threshold |
| 3 | RXA | RX FIFO Above Threshold |
| 4 | BRK | Line Break Detected |
| 5 | MATCH | Data Match Detected |
| 6 | FE | Frame Error |
| 7 | PRE | Parity Error |
| 8 | OR | Overrun |
| 9 | RTO | Receiver Timeout |

- **IM (0xFF00)**: Write 1 to enable interrupt, 0 to disable
- **RIS (0xFF08)**: Raw interrupt status (read-only)
- **MIS (0xFF04)**: Masked interrupt status (read-only)
- **IC (0xFF0C)**: Write 1 to clear interrupt (W1C)

## Example Register Access

### UART0 Register Access
```c
// Base address for UART0
#define UART0_BASE 0x30000000

// Write to UART0 TXDATA
*((volatile uint32_t*)(UART0_BASE + 0x0004)) = 'A';

// Read from UART0 RXDATA
uint32_t data = *((volatile uint32_t*)(UART0_BASE + 0x0000));
```

### UART1 Register Access
```c
// Base address for UART1
#define UART1_BASE 0x30010000

// Write to UART1 TXDATA
*((volatile uint32_t*)(UART1_BASE + 0x0004)) = 'B';

// Read from UART1 RXDATA
uint32_t data = *((volatile uint32_t*)(UART1_BASE + 0x0000));
```

## Invalid Address Handling

- Reads to invalid addresses return: `0xDEADBEEF`
- Writes to invalid addresses are acknowledged but discarded
- All valid transactions receive a Wishbone ACK

## Notes

1. **Clock Gating**: The GCLK register is present in CF_UART but **clock gating is disabled** for Caravel integration. The clock is always enabled.

2. **Byte-Lane Writes**: All registers support byte-lane writes via `wbs_sel_i[3:0]`.

3. **Register Width**: All registers are 32-bit aligned, even if they use fewer bits.

4. **Interrupt Routing**: UART interrupts are routed to Caravel `user_irq[2:0]` signals (implementation details in integration_notes.md).

---
**Last Updated**: 2025-11-01
