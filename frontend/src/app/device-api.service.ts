import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Device, DeviceCreate, DeviceState } from './device.model';

@Injectable({ providedIn: 'root' })
export class DeviceApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/devices';

  list(): Observable<Device[]> {
    return this.http.get<Device[]>(this.baseUrl);
  }

  add(device: DeviceCreate): Observable<Device> {
    return this.http.post<Device>(this.baseUrl, device);
  }

  remove(ip: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${ip}`);
  }

  check(ip: string): Observable<{ reachable: boolean }> {
    return this.http.post<{ reachable: boolean }>(`${this.baseUrl}/check`, { ip });
  }

  state(ip: string): Observable<DeviceState> {
    return this.http.get<DeviceState>(`${this.baseUrl}/${ip}/state`);
  }

  turnOn(ip: string): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/${ip}/on`, {});
  }

  turnOff(ip: string): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/${ip}/off`, {});
  }

  setAll(action: 'on' | 'off'): Observable<{ failed: string[] }> {
    return this.http.post<{ failed: string[] }>(`${this.baseUrl}/all/${action}`, {});
  }

  setColor(ip: string, color: [number, number, number]): Observable<void> {
    const [red, green, blue] = color;
    return this.http.put<void>(`${this.baseUrl}/${ip}/color`, { red, green, blue });
  }

  setBrightness(ip: string, brightness: number): Observable<void> {
    return this.http.put<void>(`${this.baseUrl}/${ip}/brightness`, { brightness });
  }
}
