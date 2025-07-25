#!/bin/bash
# ALSA Dependencies Installation Script for Raspberry Pi
# Optimizes system for low-latency audio with INTA AI

echo "🔧 Installing ALSA Dependencies for Low-Latency Audio"
echo "=================================================="

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install ALSA dependencies
echo "🎵 Installing ALSA audio system..."
sudo apt install -y python3-alsaaudio alsa-utils

# Install additional audio dependencies
echo "🔊 Installing additional audio dependencies..."
sudo apt install -y portaudio19-dev python3-pyaudio

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install webrtcvad pyalsaaudio

# Optimize ALSA configuration for low latency
echo "⚡ Optimizing ALSA for low latency..."

# Create optimized ALSA configuration
sudo tee /etc/asound.conf > /dev/null <<EOF
# Low-latency ALSA configuration for Raspberry Pi
pcm.!default {
    type plug
    slave.pcm "hw:0,0"
}

ctl.!default {
    type hw
    card 0
}

# Optimize for low latency
pcm.lowlatency {
    type plug
    slave.pcm "hw:0,0"
    slave.rate 8000
    slave.channels 1
    slave.format S16_LE
    slave.period_size 512
    slave.buffer_size 2048
}
EOF

# Set audio group permissions
echo "🔐 Setting audio permissions..."
sudo usermod -a -G audio $USER

# Optimize system for real-time audio
echo "⚡ Optimizing system for real-time audio..."

# Add real-time priority settings
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
# Real-time audio priority for INTA AI
@audio - rtprio 95
@audio - memlock unlimited
EOF

# Optimize CPU governor for performance
echo "🚀 Setting CPU governor to performance..."
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils > /dev/null

# Create systemd service for audio optimization
echo "🔧 Creating audio optimization service..."
sudo tee /etc/systemd/system/audio-optimization.service > /dev/null <<EOF
[Unit]
Description=Audio Optimization for INTA AI
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
ExecStart=/bin/bash -c 'echo 95 | sudo tee /proc/sys/vm/swappiness'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl enable audio-optimization.service

# Test ALSA installation
echo "🧪 Testing ALSA installation..."
if python3 -c "import alsaaudio; print('✅ ALSA Python library working')" 2>/dev/null; then
    echo "✅ ALSA Python library installed successfully"
else
    echo "❌ ALSA Python library installation failed"
    exit 1
fi

# Test VAD installation
echo "🎤 Testing Voice Activity Detection..."
if python3 -c "import webrtcvad; print('✅ WebRTC VAD working')" 2>/dev/null; then
    echo "✅ WebRTC VAD installed successfully"
else
    echo "❌ WebRTC VAD installation failed"
    exit 1
fi

# List available audio devices
echo "📋 Available audio devices:"
aplay -l

echo ""
echo "🎉 ALSA Dependencies Installation Complete!"
echo ""
echo "📋 Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. Test the installation: python3 test_alsa_inta.py"
echo "3. Start INTA AI: python3 main.py"
echo ""
echo "💡 Tips for optimal performance:"
echo "- Use a USB microphone for better quality"
echo "- Keep the system cool for best performance"
echo "- Monitor CPU usage during audio processing"
echo ""
echo "🔧 Troubleshooting:"
echo "- If audio doesn't work, check: alsamixer"
echo "- To test microphone: arecord -d 5 test.wav && aplay test.wav"
echo "- To see ALSA devices: cat /proc/asound/cards" 