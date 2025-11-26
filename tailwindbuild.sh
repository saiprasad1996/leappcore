#!/bin/bash
# Build Tailwind CSS
# For development with watch mode: ./tailwindbuild.sh --watch
# For production build: ./tailwindbuild.sh

if [ "$1" = "--watch" ]; then
  tailwindcss -i leappcore/public/css/tailwind.css -o leappcore/public/css/styles.prod.css --watch
else
  tailwindcss -i leappcore/public/css/tailwind.css -o leappcore/public/css/styles.prod.css --minify
fi
