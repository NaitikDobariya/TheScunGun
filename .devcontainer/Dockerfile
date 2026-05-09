FROM osrf/ros:humble-desktop

# Avoid user interaction during apt installations
ENV DEBIAN_FRONTEND=noninteractive

# 1. Update and install basic dependencies, Build Tools, & QoL
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-setuptools \
    python3-colcon-common-extensions \
    python3-rosdep \
    tmux \
    git \
    nano \
    vim \
    bash-completion \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. NVIDIA & Graphics Support
RUN apt-get update && apt-get install -y --no-install-recommends \
    mesa-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 3. Simulation, Modeling, and ROS 2 Control (Ignition Fortress + ROS 2 Bridge)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-ros-gz \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    ros-humble-joint-state-publisher-gui \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-ign-ros2-control \
    && rm -rf /var/lib/apt/lists/*

# 4. Navigation 2 & Mapping
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------
# 6. SCUN-GUN BRAIN: Pre-compiled Cartographer & 2D-to-3D Bridge Tools
# Zero compiling required. This bypasses the RAM/Hanging issues entirely.
# -----------------------------------------------------------------------
    RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-cartographer \
    ros-humble-cartographer-ros \
    ros-humble-cartographer-rviz \
    ros-humble-laser-geometry \
    ros-humble-pcl-conversions \
    ros-humble-perception-pcl \
    ros-humble-pointcloud-to-laserscan \
    && rm -rf /var/lib/apt/lists/*
# -----------------------------------------------------------------------

# 5. User Management (Non-root user)
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && usermod -aG dialout,video $USERNAME

# Auto-source ROS 2 in the container terminal
RUN echo "source /opt/ros/humble/setup.bash" >> /home/$USERNAME/.bashrc

# Switch to the non-root user
USER $USERNAME
WORKDIR /home/$USERNAME/scun_gun_ws