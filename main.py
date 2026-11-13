import zlib
import struct
import os

def make_chunk(chunk_type, chunk_data):
    """Creates a PNG chunk with length, type, data, and CRC."""
    length = struct.pack('>I', len(chunk_data))
    # CRC is calculated over chunk type and chunk data
    crc = struct.pack('>I', zlib.crc32(chunk_type + chunk_data) & 0xffffffff)
    return length + chunk_type + chunk_data + crc

def create_png(width, height, raw_pixels):
    """
    Encodes raw RGB pixels into a PNG file.
    raw_pixels should be a bytearray of size width * height * 3.
    """
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk: Width (4), Height (4), Bit depth (1), Color type (1), 
    # Compression (1), Filter (1), Interlace (1)
    # Color type 2 is RGB.
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = make_chunk(b'IHDR', ihdr_data)
    
    # IDAT chunk: Compressed image data.
    # Each scanline must be preceded by a filter type byte (0 for None).
    scanlines = bytearray()
    for y in range(height):
        scanlines.append(0)  # Filter type 0
        start = y * width * 3
        end = start + width * 3
        scanlines.extend(raw_pixels[start:end])
    
    compressed_idat = zlib.compress(scanlines, level=9)
    idat_chunk = make_chunk(b'IDAT', compressed_idat)
    
    # IEND chunk
    iend_chunk = make_chunk(b'IEND', b'')
    
    return signature + ihdr_chunk + idat_chunk + iend_chunk

def draw_circle(buffer, width, height, cx, cy, r, color):
    """Draws a solid circle into the RGB buffer."""
    for y in range(max(0, cy - r), min(height, cy + r + 1)):
        for x in range(max(0, cx - r), min(width, cx + r + 1)):
            if (x - cx)**2 + (y - cy)**2 <= r**2:
                idx = (y * width + x) * 3
                buffer[idx:idx+3] = color

def draw_rect(buffer, width, height, x1, y1, x2, y2, color):
    """Draws a solid rectangle into the RGB buffer."""
    for y in range(max(0, y1), min(height, y2)):
        start_idx = (y * width + max(0, x1)) * 3
        end_idx = (y * width + min(width, x2)) * 3
        # Fast way to fill a range in bytearray
        row_len = (min(width, x2) - max(0, x1))
        buffer[start_idx:end_idx] = bytes(color) * row_len

def main():
    width, height = 1024, 1024
    buffer = bytearray(width * height * 3)
    
    # 1. Refined Sky Gradient (Deep Blue to Light Blue)
    # Using float interpolation for smoother steps
    c1, c2 = (0, 0, 128), (135, 206, 235)
    for y in range(height):
        factor = y / (height - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * factor)
        g = int(c1[1] + (c2[1] - c1[1]) * factor)
        b = int(c1[2] + (c2[2] - c1[2]) * factor)
        buffer[y * width * 3 : (y + 1) * width * 3] = bytes([r, g, b]) * width

    # 2. Rainbow (5 colors)
    rb_colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255)]
    rb_cx, rb_cy = 512, 850
    for i, color in enumerate(rb_colors):
        radius = 750 - (i * 20)
        for r_inner in range(radius, radius - 20, -1):
            for x in range(width):
                dy2 = r_inner**2 - (x - rb_cx)**2
                if dy2 >= 0:
                    dy = int(dy2**0.5)
                    y_top = rb_cy - dy
                    if 0 <= y_top < height:
                        idx = (y_top * width + x) * 3
                        buffer[idx:idx+3] = color

    # 3. Clouds (White)
    for cx, cy in [(250, 250), (600, 180), (850, 300)]:
        for dx, dy, r in [(0,0,50), (-40,10,40), (40,10,40), (-20,-20,35), (20,-20,35)]:
            draw_circle(buffer, width, height, cx + dx, cy + dy, r, (255, 255, 255))

    # 4. Hills (Darker Green)
    hill_color = (0, 100, 0)
    for hx, hy, hr in [(300, 950, 400), (800, 950, 350)]:
        draw_circle(buffer, width, height, hx, hy, hr, hill_color)

    # 5. Wavy Grass
    for x in range(width):
        phase = (x % 250) / 250
        wave_y = 820 + int(40 * ((phase if phase < 0.5 else 1 - phase) * 4 - 1))
        for y in range(wave_y, height):
            idx = (y * width + x) * 3
            buffer[idx:idx+3] = (34, 139, 34)

    # 6. Butterflies (3 Small Colorful Ones)
    # Positions and colors for butterflies
    bfly_data = [
        (400, 750, (255, 105, 180)), # Pink
        (700, 780, (173, 216, 230)), # Light Blue
        (200, 800, (255, 215, 0))    # Gold
    ]
    for bx, by, bcol in bfly_data:
        # Body
        draw_rect(buffer, width, height, bx - 1, by - 8, bx + 1, by + 8, (0, 0, 0))
        # Wings (circles)
        draw_circle(buffer, width, height, bx - 10, by - 5, 8, bcol)
        draw_circle(buffer, width, height, bx + 10, by - 5, 8, bcol)
        draw_circle(buffer, width, height, bx - 8, by + 5, 6, bcol)
        draw_circle(buffer, width, height, bx + 8, by + 5, 6, bcol)

    # 7. Cheerful Sun
    sun_x, sun_y, sun_r = 120, 120, 70
    draw_circle(buffer, width, height, sun_x, sun_y, sun_r, (255, 255, 0))
    draw_circle(buffer, width, height, sun_x - 20, sun_y - 15, 7, (0, 0, 0))
    draw_circle(buffer, width, height, sun_x + 20, sun_y - 15, 7, (0, 0, 0))
    for dx in range(-25, 26):
        dy = (dx * dx) // 30 + 15
        draw_circle(buffer, width, height, sun_x + dx, sun_y + dy, 4, (0, 0, 0))

    # 8. Flowers
    flower_colors = [(255, 20, 147), (255, 255, 255), (148, 0, 211), (255, 165, 0), (0, 255, 255)]
    for i in range(20):
        fx = (i * 53 + 100) % 1024
        fy = 860 + (i * 17) % 130
        draw_rect(buffer, width, height, fx - 2, fy - 25, fx + 2, fy, (0, 80, 0))
        p_color = flower_colors[i % len(flower_colors)]
        draw_circle(buffer, width, height, fx, fy - 30, 10, p_color)
        draw_circle(buffer, width, height, fx, fy - 30, 3, (255, 255, 0))

    # Save to PNG
    png_data = create_png(width, height, buffer)
    
    output_path = '/output/entry.png'
    if not os.path.exists('/output') or not os.access('/output', os.W_OK):
        output_path = './output/entry.png'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
    with open(output_path, 'wb') as f:
        f.write(png_data)
        
    print(f"File: {output_path}")
    print(f"Dimensions: {width}x{height}")
    print(f"Size: {len(png_data)} bytes ({len(png_data) / 1024 / 1024:.4f} MiB)")

if __name__ == '__main__':
    main()
