# Chiedi all'utente se vuole esportare le immagini Docker
read -p "Build Backend: (S/N)" build_backend
read -p "Build Actions: (S/N)" build_actions
read -p "Build Frontend: (S/N)" build_frontend
read -p "Vuoi esportare l'immagine Docker? (S/N): " export_images
read -p "Specifica il tag per le immagini Docker (latest/stable): " docker_tag
read -p "Lanciare l'applicazione al termine (S/N): " start_application

# Converte la risposta in maiuscolo per una corretta gestione
export_images=$(echo "$export_images" | tr '[:lower:]' '[:upper:]')
build_backend=$(echo "$build_backend" | tr '[:lower:]' '[:upper:]')
build_actions=$(echo "$build_actions" | tr '[:lower:]' '[:upper:]')
build_frontend=$(echo "$build_frontend" | tr '[:lower:]' '[:upper:]')
start_application=$(echo "$start_application" | tr '[:lower:]' '[:upper:]')

CURRENT_DIR=$(pwd)

# Verifica se il tag è valido
if [[ "$docker_tag" != "latest" && "$docker_tag" != "stable" ]]; then
  echo "Tag non valido. Usa 'latest' o 'stable'."
  exit 1
fi

cd "$CURRENT_DIR"

if [ "$build_backend" == "S" ]; then
  echo "Start building armando_backend"
  cd backend
  docker image rm -f  armando_backend:"$docker_tag"
  docker build --force-rm -t armando_backend:"$docker_tag" .
  echo "End building armando_backend"
  if [ "$export_images" == "S" ]; then
    echo "Start export armando_backend"
    docker save -o armando_backend_"$docker_tag".tar armando_backend:"$docker_tag"
    mv armando_backend_"$docker_tag".tar ..
    echo "End export armando_backend"
  fi
fi

cd "$CURRENT_DIR"

if [ "$build_frontend" == "S" ]; then
  echo "Start building armando_frontend"
  cd frontend
  docker image rm -f armando_frontend:"$docker_tag"
  docker build --force-rm -t armando_frontend:"$docker_tag" .
  echo "End building armando_frontend"
  if [ "$export_images" == "S" ]; then
    echo "Start export armando_frontend"
    docker save -o armando_frontend_"$docker_tag".tar armando_frontend:"$docker_tag"
    mv armando_frontend_"$docker_tag".tar ..
    echo "End export armando_frontend"
  fi
fi

cd "$CURRENT_DIR"

if [ "$build_actions" == "S" ]; then
  echo "Start building armando_actions"
  cd actions
  docker image rm -f armando_actions:"$docker_tag"
  docker build --force-rm -t armando_actions:"$docker_tag" .
  echo "End building armando_actions"
  if [ "$export_images" == "S" ]; then
    echo "Start export armando_actions"
    docker save -o armando_actions_"$docker_tag".tar armando_actions:"$docker_tag"
    mv armando_actions_"$docker_tag".tar ..
    echo "End export armando_actions"
  fi
fi

cd "$CURRENT_DIR"

if [ "$start_application" == "S" ]; then
  docker compose up -d 
fi