import { AfterViewInit, Component, ElementRef, OnInit, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';

import { DeviceApiService } from './device-api.service';
import { Device, DeviceCreate } from './device.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit, AfterViewInit {
  private readonly api = inject(DeviceApiService);
  @ViewChild('wheel') private wheel?: ElementRef<HTMLCanvasElement>;

  devices: Device[] = [];
  selectedDevice: Device | undefined;
  selectedColor: [number, number, number] = [255, 255, 255];
  brightness = 100;
  isOn = false;
  loading = false;
  managerOpen = false;
  darkMode = false;
  checking = false;
  message = '';
  error = '';
  newDevice: DeviceCreate = { name: '', ip: '', type: 'Flux', color_order: 'RGB' };

  ngOnInit(): void {
    this.darkMode = localStorage.getItem('magic-home-theme') !== 'light';
    this.loadDevices();
  }

  toggleTheme(): void {
    this.darkMode = !this.darkMode;
    localStorage.setItem('magic-home-theme', this.darkMode ? 'dark' : 'light');
  }

  ngAfterViewInit(): void {
    this.drawColorWheel();
  }

  loadDevices(): void {
    this.error = '';
    this.api.list().subscribe({
      next: (devices) => {
        this.devices = devices;
        const selected = devices.find(device => device.ip === this.selectedDevice?.ip);
        if (selected) {
          this.selectedDevice = selected;
        } else if (devices.length > 0) {
          this.selectDevice(devices[0]);
        }
      },
      error: () => this.error = 'The backend could not be reached.'
    });
  }

  selectDevice(device: Device): void {
    this.selectedDevice = device;
    this.loading = true;
    this.error = '';
    this.api.state(device.ip).pipe(finalize(() => this.loading = false)).subscribe({
      next: (state) => {
        this.isOn = state.is_on;
        this.selectedColor = state.color;
        this.brightness = state.brightness;
        setTimeout(() => this.drawColorWheel());
      },
      error: () => this.error = `Could not read ${device.name}.`
    });
  }

  toggle(): void {
    if (!this.selectedDevice) return;
    const request = this.isOn
      ? this.api.turnOff(this.selectedDevice.ip)
      : this.api.turnOn(this.selectedDevice.ip);
    request.subscribe({
      next: () => this.isOn = !this.isOn,
      error: () => this.error = 'The bulb did not accept the command.'
    });
  }

  powerAll(action: 'on' | 'off'): void {
    this.loading = true;
    this.api.setAll(action).pipe(finalize(() => this.loading = false)).subscribe({
      next: (result) => {
        this.message = result.failed.length ? `Failed: ${result.failed.join(', ')}` : `All devices turned ${action}.`;
        if (this.selectedDevice) this.selectDevice(this.selectedDevice);
      },
      error: () => this.error = 'The group command failed.'
    });
  }

  setColor(): void {
    if (!this.selectedDevice) return;
    this.api.setColor(this.selectedDevice.ip, this.selectedColor).subscribe({
      error: () => this.error = 'The color could not be changed.'
    });
  }

  setBrightness(value: string): void {
    if (!this.selectedDevice) return;
    const brightness = Number(value);
    this.brightness = brightness;
    this.api.setBrightness(this.selectedDevice.ip, brightness).subscribe({
      error: () => this.error = 'The brightness could not be changed.'
    });
  }

  pickColor(event: PointerEvent): void {
    const wheel = event.currentTarget as HTMLCanvasElement;
    const bounds = wheel.getBoundingClientRect();
    const x = event.clientX - bounds.left - bounds.width / 2;
    const y = event.clientY - bounds.top - bounds.height / 2;
    const radius = bounds.width / 2;
    const distance = Math.sqrt(x * x + y * y);
    if (distance > radius) return;

    const hue = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
    const saturation = distance / radius;
    this.selectedColor = this.hsvToRgb(hue / 360, saturation, 1);
    this.drawColorWheel();
    this.setColor();
  }

  private drawColorWheel(): void {
    const canvas = this.wheel?.nativeElement;
    if (!canvas) return;
    const size = canvas.clientWidth || 300;
    canvas.width = size;
    canvas.height = size;
    const context = canvas.getContext('2d');
    if (!context) return;

    const image = context.createImageData(size, size);
    const radius = size / 2;
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        const dx = x - radius;
        const dy = y - radius;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const offset = (y * size + x) * 4;
        if (distance > radius) {
          image.data[offset + 3] = 0;
          continue;
        }
        const hue = (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;
        const color = this.hsvToRgb(hue / 360, distance / radius, 1);
        image.data[offset] = color[0];
        image.data[offset + 1] = color[1];
        image.data[offset + 2] = color[2];
        image.data[offset + 3] = 255;
      }
    }
    context.putImageData(image, 0, 0);

    const [red, green, blue] = this.selectedColor.map(value => value / 255);
    const markerHue = this.rgbToHue(red, green, blue);
    const saturation = Math.max(red, green, blue) === 0 ? 0 : (Math.max(red, green, blue) - Math.min(red, green, blue)) / Math.max(red, green, blue);
    const markerRadius = saturation * radius;
    const angle = markerHue * Math.PI * 2;
    context.beginPath();
    context.arc(radius + markerRadius * Math.cos(angle), radius + markerRadius * Math.sin(angle), 7, 0, Math.PI * 2);
    context.strokeStyle = '#ffffff';
    context.lineWidth = 3;
    context.stroke();
  }

  private rgbToHue(red: number, green: number, blue: number): number {
    const maximum = Math.max(red, green, blue);
    const minimum = Math.min(red, green, blue);
    const difference = maximum - minimum;
    if (difference === 0) return 0;
    let hue = 0;
    if (maximum === red) hue = ((green - blue) / difference) % 6;
    else if (maximum === green) hue = (blue - red) / difference + 2;
    else hue = (red - green) / difference + 4;
    return (hue / 6 + 1) % 1;
  }

  private hsvToRgb(hue: number, saturation: number, value: number): [number, number, number] {
    const sector = hue * 6;
    const index = Math.floor(sector);
    const fraction = sector - index;
    const p = value * (1 - saturation);
    const q = value * (1 - fraction * saturation);
    const t = value * (1 - (1 - fraction) * saturation);
    const colors = [[value, t, p], [q, value, p], [p, value, t], [p, q, value], [t, p, value], [value, p, q]];
    const color = colors[index % 6];
    return color.map(channel => Math.round(channel * 255)) as [number, number, number];
  }

  checkDevice(): void {
    this.checking = true;
    this.message = '';
    this.error = '';
    this.api.check(this.newDevice.ip).pipe(finalize(() => this.checking = false)).subscribe({
      next: (result) => this.message = result.reachable ? 'Device responded.' : 'Device did not respond.',
      error: (error: { error?: { detail?: string } }) => this.error = error.error?.detail || 'Device could not be reached.'
    });
  }

  addDevice(): void {
    this.error = '';
    this.message = '';
    this.api.add(this.newDevice).subscribe({
      next: (device) => {
        this.devices = [...this.devices, device];
        this.newDevice = { name: '', ip: '', type: 'Flux', color_order: 'RGB' };
        this.message = 'Device added.';
      },
      error: (error: { error?: { detail?: string } }) => this.error = error.error?.detail || 'Device could not be added.'
    });
  }

  removeDevice(device: Device): void {
    if (!confirm(`Remove ${device.name}?`)) return;
    this.api.remove(device.ip).subscribe({
      next: () => {
        this.devices = this.devices.filter(item => item.ip !== device.ip);
        if (this.selectedDevice?.ip === device.ip) {
          this.selectedDevice = this.devices[0];
          if (this.selectedDevice) this.selectDevice(this.selectedDevice);
        }
        this.message = 'Device removed.';
      },
      error: () => this.error = 'Device could not be removed.'
    });
  }

  colorHex(): string {
    return '#' + this.selectedColor
      .map(value => value.toString(16).padStart(2, '0'))
      .join('');
  }

  colorChanged(value: string): void {
    const hex = value.replace('#', '');
    this.selectedColor = [
      parseInt(hex.slice(0, 2), 16),
      parseInt(hex.slice(2, 4), 16),
      parseInt(hex.slice(4, 6), 16)
    ] as [number, number, number];
    this.setColor();
  }
}
