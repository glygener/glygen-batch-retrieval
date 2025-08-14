
Edit conf/config.json and run the following

1) Create image
```
$ python3 create_image.py
```

2) Create container
```	
$ python3 create_container.py
```


3) Create service for controlling the container
Edit /usr/lib/systemd/system/docker-glygen-retriever.service and
place the following content in it.
```
[Unit]
Description=Glygen Retriver Container
Requires=docker.service
After=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker start -a running_glygen_retriever
ExecStop=/usr/bin/docker stop -t 2 running_glygen_retriever

[Install]
WantedBy=default.target
```

This will allow you to start/stop the container with the following commands, and ensure
that the container will start on server reboot.
```
   $ sudo systemctl daemon-reload
   $ sudo systemctl enable docker-glygen-retriever.service
   $ sudo systemctl start docker-glygen-retriever.service
   $ sudo systemctl stop docker-glygen-retriever.service
```

Or manuall start as

```	
$ docker run -itd -v /data/shared/glygen:/data/shared/glygen --name running_glygen_retriever glygen/retriever
```

4) Running the container
```
$ docker exec -t running_glygen_retriever python /app/retriever.py -i /data/shared/glygen/tmp/input.2.json -o /data/shared/glygen/tmp/output.2.json 
```



