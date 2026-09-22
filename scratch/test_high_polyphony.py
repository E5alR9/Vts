# -*- coding: utf-8 -*-
import pygame
import pygame.midi
import time

def test_multi_channel_midi():
    print("Testing multi-channel high polyphony MIDI...")
    pygame.midi.init()
    out_id = pygame.midi.get_default_output_id()
    print("Default Output ID:", out_id)
    if out_id == -1:
        print("No MIDI output device found")
        return
    out = pygame.midi.Output(out_id)
    channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]
    for ch in channels:
        out.set_instrument(0, channel=ch)
        out.write_short(0xB0 + ch, 7, 127)
        out.write_short(0xB0 + ch, 72, 60)
        
    print("Simulating rapid-fire Rush E notes (50 notes in 0.5s)...")
    for i in range(50):
        ch = channels[i % len(channels)]
        out.note_on(64, 110, ch)  # E4 note
        time.sleep(0.01)
        if i >= 5:
            old_ch = channels[(i - 5) % len(channels)]
            out.note_off(64, 0, old_ch)
            
    time.sleep(0.5)
    for ch in channels:
        out.write_short(0xB0 + ch, 123, 0)
    print("Success!")
    out.close()
    pygame.midi.quit()

if __name__ == "__main__":
    test_multi_channel_midi()
