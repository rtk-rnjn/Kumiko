#!/usr/bin/env bash

# if [[ -v KUMIKO_TOKEN ]]; then
#     echo "KUMIKO_TOKEN=${KUMIKO_TOKEN}" >> /Kumiko/Bot/.env
# else
#     echo "Missing Kumiko's bot token! KUMIKO_TOKEN environment variable is not set."
#     exit 1;
# fi

# Testing bot token
# Not needed in production
# if [[ -v DEV_BOT_TOKEN ]]; then
#     echo "DEV_BOT_TOKEN=${DEV_BOT_TOKEN}" >> /Kumiko/Bot/.env
# fi 

# API Keys
# GitHub
# if [[ -v GITHUB_API_ACCESS_TOKEN ]]; then
#     echo "GitHub_API_Access_Token=${GITHUB_API_ACCESS_TOKEN}" >> /Kumiko/Bot/.env
# else
#     echo "Missing GitHub API token! GITHUB_API_ACCESS_TOKEN environment variable is not set."
# fi 
# # Reddit ID
# if [[ -v REDDIT_ID ]]; then
#     echo "Reddit_ID=${REDDIT_ID}" >> /Kumiko/Bot/.env
# else
#     echo "Missing Reddit ID! REDDIT_ID environment variable is not set."
# fi 
# # Reddit Secret
# if [[ -v REDDIT_SECRET ]]; then
#     echo "Reddit_Secret=${REDDIT_SECRET}" >> /Kumiko/Bot/.env
# else
#     echo "Missing Reddit secret! REDDIT_SECRET environment variable is not set."
# fi 
# # Tenor
# if [[ -v TENOR_API_KEY ]]; then
#     echo "Kumiko_Tenor_API_Key=${TENOR_API_KEY}" >> /Kumiko/Bot/.env
# else
#     echo "Missing Tenor API key! TENOR_API_KEY environment variable is not set."
# fi 
# YouTube

# if [[ -v IPC_SECRET_KEY ]]; then
#     echo "IPC_SECRET_KEY=${IPC_SECRET_KEY}" >> /Kumiko/Bot/.env
# else
#     echo "Missing IPC_Secret_Key env var! IPC_Secret_Key environment variable is not set."
#     exit 1;
# fi

# if [[ -v DATABASE_URL ]]; then
#     echo "DATABASE_URL=${DATABASE_URL}" >> /Kumiko/Bot/.env
# else
#     echo "Missing DATABASE_URL env var! DATABASE_URL environment variable is not set."
#     exit 1;
# fi

KUMIKO_FIRST_START_CHECK="KUMIKO_FIRST_START"

if [ ! -f $KUMIKO_FIRST_START_CHECK ]; then
    touch $KUMIKO_FIRST_START_CHECK
    echo 'DO NOT EDIT THIS FILE! THIS IS USED WHEN YOU FIRST RUN KUMIKO USING DOCKER!' >> $KUMIKO_FIRST_START_CHECK
    exec python3 /Kumiko/migrations-runner.py
fi

exec python3 /Kumiko/Bot/kumikobot.py