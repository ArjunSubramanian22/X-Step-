/** 28-byte X-Step BLE packet — keep in lockstep with xstep_ml/protocol.py */

export const PACKET_SIZE = 28;
export const GATT_SERVICE_UUID = '6e400001-b5a3-f393-e0a9-e50e24dcca9e';
export const GATT_TX_UUID = '6e400003-b5a3-f393-e0a9-e50e24dcca9e';
export const GATT_RX_UUID = '6e400002-b5a3-f393-e0a9-e50e24dcca9e';
export const DEVICE_PREFIX = 'XSTEP';
export const ADC_FULL_SCALE = 4095;
export const KPA_FULL_SCALE = 250;

export interface DecodedPacket {
  side: 'left' | 'right';
  seq: number;
  tMs: number;
  adc: [number, number, number, number];
  kpa: [number, number, number, number];
  battery: number;
  charging: boolean;
  temperaturesC: [number, number, number, number] | null;
}

export function adcToKpa(adc: number, baseline = 0): number {
  return (Math.max(0, adc - baseline) / ADC_FULL_SCALE) * KPA_FULL_SCALE;
}

export function decodePacket(
  bytes: Uint8Array,
  baseline: [number, number, number, number] = [0, 0, 0, 0]
): DecodedPacket {
  if (bytes.length < PACKET_SIZE) {
    throw new Error('short packet');
  }
  if (bytes[0] !== 0x58 || bytes[1] !== 0x53) {
    throw new Error('bad magic');
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const flags = bytes[3];
  const seq = view.getUint16(4, true);
  const tMs = view.getUint32(6, true);
  const adc: [number, number, number, number] = [
    view.getUint16(10, true),
    view.getUint16(12, true),
    view.getUint16(14, true),
    view.getUint16(16, true),
  ];
  const kpa: [number, number, number, number] = [
    adcToKpa(adc[0], baseline[0]),
    adcToKpa(adc[1], baseline[1]),
    adcToKpa(adc[2], baseline[2]),
    adcToKpa(adc[3], baseline[3]),
  ];
  let temperaturesC: [number, number, number, number] | null = null;
  if (flags & 4) {
    temperaturesC = [
      view.getInt16(20, true) / 10,
      view.getInt16(22, true) / 10,
      view.getInt16(24, true) / 10,
      view.getInt16(26, true) / 10,
    ];
  }
  return {
    side: flags & 1 ? 'left' : 'right',
    seq,
    tMs,
    adc,
    kpa,
    battery: bytes[18],
    charging: Boolean(flags & 8),
    temperaturesC,
  };
}
