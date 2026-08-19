import { decodePacket, DEVICE_PREFIX, GATT_SERVICE_UUID, GATT_TX_UUID, type DecodedPacket } from '@/services/protocol';

export type BleListener = (packet: DecodedPacket) => void;

/**
 * BLE insole client. Uses a dynamic import so Expo web / simulator builds
 * still run when native BLE is unavailable. Pair devices named XSTEP-L / XSTEP-R.
 */
export async function startInsoleScan(onPacket: BleListener): Promise<() => void> {
  try {
    const ble = await import('react-native-ble-plx').catch(() => null);
    if (!ble) {
      return () => undefined;
    }
    const { BleManager } = ble;
    const manager = new BleManager();
    const sub = manager.onStateChange((state: string) => {
      if (state === 'PoweredOn') {
        manager.startDeviceScan(null, { allowDuplicates: true }, (err: Error | null, device: { name?: string | null; serviceUUIDs?: string[] | null }) => {
          if (err || !device?.name?.startsWith(DEVICE_PREFIX)) return;
          deviceConnect(manager, device, onPacket);
        });
      }
    }, true);
    return () => {
      sub.remove();
      manager.stopDeviceScan();
      manager.destroy();
    };
  } catch {
    return () => undefined;
  }
}

function deviceConnect(manager: { connectToDevice: Function }, device: { id: string; monitorCharacteristicForService?: Function }, onPacket: BleListener) {
  manager
    .connectToDevice(device.id)
    .then((d: { discoverAllServicesAndCharacteristics: () => Promise<{ monitorCharacteristicForService: Function }> }) =>
      d.discoverAllServicesAndCharacteristics()
    )
    .then((d: { monitorCharacteristicForService: Function }) => {
      d.monitorCharacteristicForService(GATT_SERVICE_UUID, GATT_TX_UUID, (_e: unknown, char: { value?: string | null }) => {
        if (!char?.value) return;
        const raw = Uint8Array.from(atob(char.value), (c) => c.charCodeAt(0));
        try {
          onPacket(decodePacket(raw));
        } catch {
          /* ignore malformed */
        }
      });
    })
    .catch(() => undefined);
}
