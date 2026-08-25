export interface Device {
  name: string;
  ip: string;
  type: string;
  color_order: string;
}

export interface DeviceState {
  ip: string;
  is_on: boolean;
  color: [number, number, number];
  brightness: number;
}

export interface DeviceCreate {
  name: string;
  ip: string;
  type: string;
  color_order: string;
}
