# Proyecto pipeline red social

## Descripción

En este proyecto se llevará a cabo una simulación de red social en donde las interacciones de los usuarios deben ser notificadas (likes, comentarios, seguidores).

## Tecnologías utilizadas
Se utilizaron las siguientes tecnologías.
- Docker / Docker Compose
- Python / FastApi
- MySQL

## Cómo ejecutar el proyecto
A continuación se detallará el paso a paso para ejecutar el proyecto.
1. Clonar el repositorio `git clone https://github.com/sebaLcode/red_social_pipeline`.
2. Entrar al repositorio `cd red_social_pipeline`.
3. Abrir cmd y copiar el .env.example y renombrar a .env `copy .env.example .env`.
4. Modificar el .env con los datos deseados.
5. Teniendo Docker Desktop ejecutandose, en la misma cmd abierta `docker-compose up --build` (Si en el transcurso del proyecto, se cambian dependencias se debe hacer nuevamente el build), si ya se realizó el build, entonces ocupar `docker-compose up`.
6. En un navegador escribir `http://localhost:8080/docs`.  
7. Una vez terminada la ejecución, para apagar y eliminar el container `docker-compose down`.