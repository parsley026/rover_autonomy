FROM alvarobajceps/ros-rover-base:autonomy-rocm-beta

USER root

# Dockerfile for ROS-JAZZY
ARG USERNAME='rex'
ARG PASSWORD='changeme'
ARG SSH_PORT=22

# Default configuration
ENV ROS_ENABLE_AUTOSTART=0
ENV ROS_BUILD_ON_STARTUP=on-failure

### If really needed add only unmet pkg deps here
### Add required ros packages here
# ADDED: nodejs and npm to the end of this list
    
RUN DEBIAN_FRONTEND=noninteractive apt update && DEBIAN_FRONTEND=noninteractive apt install -y \
    ros-jazzy-image-transport ros-jazzy-image-transport-plugins ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rosbridge-suite nodejs npm xrdp tint2

RUN <<'EOF' cat > /etc/xrdp/startwm.sh
#!/bin/sh

tint2 &
exec openbox-session
EOF

RUN chmod +x /etc/xrdp/startwm.sh

# Create user
# RUN useradd -m -s /bin/bash -g 1000 ${USERNAME}
# RUN echo "${USERNAME}:${PASSWORD}" | chpasswd
# RUN usermod -aG sudo ${USERNAME}

# Change ssh port and expose it
RUN sed -i "/^#\?Port/ { s/^#//; s/Port .*/Port ${SSH_PORT}/; }" /etc/ssh/sshd_config

# Colorful prompts ah yee
# RUN sed -i 's/#force_color_prompt=yes/force_color_prompt=yes/' /home/${USERNAME}/.bashrc

# Add important stuff to bashrc
# RUN echo "\nsource /opt/ros/jazzy/setup.bash\nexport ROS_DOMAIN_ID=0\n" >> /home/${USERNAME}/.bashrc
# RUN echo "source ~/raptor_ws/install/setup.bash\n" >> /home/${USERNAME}/.bashrc

# Pass local directory to the container
USER ${USERNAME}
RUN mkdir -p /home/${USERNAME}/raptor_ws
WORKDIR /home/${USERNAME}/raptor_ws

# Copy the local files to the container
COPY --chown=${USERNAME}:${USERNAME} . /home/${USERNAME}/raptor_ws
RUN rm -rf /home/${USERNAME}/raptor_ws/build
RUN rm -rf /home/${USERNAME}/raptor_ws/log
RUN rm -rf /home/${USERNAME}/raptor_ws/install

# ADDED: Install the dashboard dependencies right after copying the files
RUN cd /home/${USERNAME}/raptor_ws/autonomy_dashboard && npm install

# Fix github 'unsafe' directory
RUN git config --global --add safe.directory /home/rex/raptor_ws
RUN git config --global --add safe.directory /home/rex/raptor_ws/src/rex_interfaces
# RUN git config --global --add safe.directory /home/rex/raptor_ws/src/libVescCan

# Look for submodules
RUN git submodule update --init --recursive || true

# Build the workspace
RUN bash -c "source /opt/ros/jazzy/setup.bash && colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --event-handlers console_start_end+ console_direct+ --executor parallel"

# Prepare .ssh directory for public keys
RUN rm -rf /home/${USERNAME}/.ssh
RUN mkdir -m 0700 /home/${USERNAME}/.ssh

USER root
COPY .devcontainer/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

CMD [ "/usr/local/bin/docker-entrypoint.sh" ]
