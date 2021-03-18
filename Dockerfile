FROM mstmelody/python-ffmpeg:20201114221500
RUN python -m pip install --upgrade pip \
 && pip --no-cache-dir install pipenv
# see: https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV PIPENV_VENV_IN_PROJECT=1
WORKDIR /workspace
# COPY ./Pipfile ./Pipfile.lock /workspace/
# RUN pipenv install --deploy --dev
COPY . /workspace
ENTRYPOINT [ "pipenv", "run" ]
CMD ["pytest"]
