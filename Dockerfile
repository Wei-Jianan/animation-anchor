FROM ubuntu:18.04

MAINTAINER wei

ENV LANG en_US.UTF-8
ENV PATH /opt/conda/bin:$PATH

RUN apt-get update && apt-get install -y wget rsync htop git openssh-server vim \
  libsm-dev libXrender* libXext*  ffmpeg sox && apt clean
# RUN apt-get install -y python3-pip  && apt clean
# RUN ln -s /usr/bin/python3 /usr/bin/python && ln -s /usr/bin/pip3 /usr/bin/pip

# install miniconda3
RUN wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py37_4.8.2-Linux-x86_64.sh -O /opt/conda3.sh \
    && echo "export PATH=/opt/conda/bin:$PATH" > /etc/profile.d/conda.sh \
    && /bin/bash /opt/conda3.sh -b -p /opt/conda \
    && echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc  \
    && echo "conda activate base" >> ~/.bashrc \
    && . ~/.bashrc \
    && conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/ \
    && conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/ \
    && conda config --set show_channel_urls yes \
    && conda update -y pip \
    && conda install -y cython \
    && rm -rf /opt/conda3.sh \
    && conda clean -y -a

# RUN apt-get install -y cmake ffmpeg  espeak espeak-data libespeak1 libespeak-dev redis python3-dev libsm-dev libXrender* libXext* &&  apt clean
# RUN pip3 install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple  && rm -rf ~/.cache/pip
#
RUN pip install numpy  opencv-python av  ffmpeg-python jieba pypinyin scipy av -i https://pypi.tuna.tsinghua.edu.cn/simple  && rm -rf ~/.cache/pip
RUN apt-get -y install build-essential gcc-multilib libx11-dev && apt clean
RUN pip install flask requests flask-cors redis -i https://pypi.tuna.tsinghua.edu.cn/simple && rm -rf ~/.cache/pip

COPY 3rdparty/htk /opt/htk
RUN cd /opt/htk && ./configure && make -j4 || make install || echo "install success"


COPY ./dist/ /opt/package/
COPY ./example /root
RUN cd /opt/package && pip install *.whl
# RUN pip install dlib  tqdm pypinyin  line_profiler Pillow setuptools -i https://pypi.tuna.tsinghua.edu.cn/simple  && rm -rf ~/.cache/pip

# RUN pip install aeneas -i https://pypi.tuna.tsinghua.edu.cn/simple && rm -rf ~/.cache/pip

# RUN apt -y install vim && apt clean

# RUN pip install ffmpeg-python jieba torch==1.1.0
