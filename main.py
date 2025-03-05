#!/usr/bin/env python3

import sys
from PIL import Image
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()


def encrypt(text, password):
    data = text.encode('utf-8')
    key = password.encode('utf-8')
    encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    return encrypted.hex()

def decrypt(encrypted_hex, password):
    try:
        encrypted = bytes.fromhex(encrypted_hex)
    except ValueError:
        console.print("[red]Error: The encrypted data is not valid hex.[/red]")
        return None
    key = password.encode('utf-8')
    decrypted_bytes = bytes([encrypted[i] ^ key[i % len(key)] for i in range(len(encrypted))])
    try:
        return decrypted_bytes.decode('utf-8')
    except UnicodeDecodeError:
        console.print("[red]Error: Incorrect password or corrupted data.[/red]")
        return None


def toBinary(text):
    bits = []
    for byte in text.encode('utf-8'):
        bits.extend(list(f"{byte:08b}"))
    return bits

def toPlain(bits):
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_str = ''.join(bits[i:i+8])
        bytes_list.append(int(byte_str, 2))
    return bytes(bytes_list).decode('utf-8', errors='replace')


def embedBit(channel, bit):
    # Check if the least significant bit of the channel is the same as the bit to be embed
    # change by max of +- 1 otherwise difference is noticeable
    
    current_bit = channel & 1
    if current_bit == bit:
    
        return channel
    else:
 
        if channel == 255:
            return channel - 1  
        elif channel == 0:
            return channel + 1  
        else:
            return channel + 1


def encodeImg(image_path, message, output_path):
    try:
        img = Image.open(image_path)
    except Exception as e:
        console.print(f"[red]Error opening image: {e}[/red]")
        return


    img = img.convert('RGBA') # RGBA For transparent and bg removed
    pixels = list(img.getdata())

  
    message_bits = toBinary(message)
    message_length = len(message_bits)
    length_bin = f"{message_length:032b}"
    data_bits = list(length_bin) + message_bits

    max_capacity = len(pixels) * 3  # max 3 bits pp
    if len(data_bits) > max_capacity:
        console.print("[red]Error: The image is too small for the message.[/red]")
        return

    new_pixels = []
    data_index = 0

    for pixel in pixels:
        r, g, b, a = pixel


        if data_index < len(data_bits):
            bit = int(data_bits[data_index])
            r = embedBit(r, bit)
            data_index += 1

        if data_index < len(data_bits):
            bit = int(data_bits[data_index])
            g = embedBit(g, bit)
            data_index += 1

        if data_index < len(data_bits):
            bit = int(data_bits[data_index])
            b = embedBit(b, bit)
            data_index += 1

        new_pixels.append((r, g, b, a))

    img.putdata(new_pixels)

    try:
        img.save(output_path)
        console.print(f"[green]Message encoded successfully into [bold]{output_path}[/bold].[/green]")
    except Exception as e:
        console.print(f"[red]Error saving image: {e}[/red]")

def decodeImg(image_path):
    """
    Decode bits from the RGBA channels of 'image_path', returning the extracted text.
    """
    try:
        img = Image.open(image_path)
    except Exception as e:
        console.print(f"[red]Error opening image: {e}[/red]")
        return None

    img = img.convert('RGBA')
    pixels = list(img.getdata())

    bits = []
    for pixel in pixels:
        r, g, b, a = pixel
    # encode for transparent 
        bits.append(str(r & 1))
        bits.append(str(g & 1))
        bits.append(str(b & 1))

 
    length_bits = bits[:32]
    message_length = int(''.join(length_bits), 2)

    
    start = 32
    end = 32 + message_length
    if end > len(bits):
        console.print("[red]Error: Not enough data to decode the full message.[/red]")
        return None

    message_bits = bits[start:end]

    try:
        message = toPlain(message_bits)
    except Exception as e:
        console.print(f"[red]Error decoding message: {e}[/red]")
        return None

    return message


def menu():
    while True:
        console.print(Panel(
            "[bold blue]CLI Steg[/bold blue]\n"
            "[green]1.[/green] Simple Encode\n"
            "[green]2.[/green] Simple Decode\n"
            "[green]3.[/green] Password-based Encode\n"
            "[green]4.[/green] Password-based Decode\n"
            "[green]5.[/green] Exit",
            title="Menu", border_style="cyan"
        ))
        choice = Prompt.ask("[yellow]What would you like to do - [/yellow]", choices=["1", "2", "3", "4", "5"])
        if choice == "1":
            image_path = Prompt.ask("[cyan]Enter path to source image[/cyan]")
            message = Prompt.ask("[cyan]Enter the message to encode[/cyan]")
            output_path = Prompt.ask("[cyan]Enter output image path[/cyan]")
            encodeImg(image_path, message, output_path)
        elif choice == "2":
            image_path = Prompt.ask("[cyan]Enter path to the image to decode[/cyan]")
            message = decodeImg(image_path)
            if message is not None:
                console.print(f"[green]Decoded message:[/green] [bold]{message}[/bold]")
        elif choice == "3":
            image_path = Prompt.ask("[cyan]Enter path to source image[/cyan]")
            message = Prompt.ask("[cyan]Enter the message to encode[/cyan]")
            password = Prompt.ask("[cyan]Enter a password[/cyan]", password=True)
            encrypted_message = encrypt(message, password)
            output_path = Prompt.ask("[cyan]Enter output image path[/cyan]")
            encodeImg(image_path, encrypted_message, output_path)
        elif choice == "4":
            image_path = Prompt.ask("[cyan]Enter path to the image to decode[/cyan]")
            encrypted_message = decodeImg(image_path)
            if encrypted_message is not None:
                password = Prompt.ask("[cyan]Enter the password[/cyan]", password=True)
                decrypted_message = decrypt(encrypted_message, password)
                if decrypted_message is not None:
                    console.print(f"[green]Decoded message:[/green] [bold]{decrypted_message}[/bold]")
        elif choice == "5":
            console.print("[magenta]Sad to see you go...[/magenta]")
            break

if __name__ == "__main__":
    menu()
