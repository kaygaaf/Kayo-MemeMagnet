# Kayo-MemeMagnet 📱

A slick Python app with a modern GUI to automatically snatch the hottest memes and videos from Reddit and repost them to X. Built for tech tinkerers who love automating viral content! 

<img width="718" height="578" alt="Screenshot 2025-08-05 at 17 28 38" src="https://github.com/user-attachments/assets/7c9bd181-2da0-4425-a153-18ffa7cd6c9e" />

## Features 🚀
- **Content Magnetism**: Pulls top memes/videos from multiple subreddits (e.g., r/memes, r/dankmemes) with a minimum upvote filter.
- **Smart Reposting**: Posts to X with Reddit source attribution, avoiding duplicates with a local tracker.
- **Modern GUI**: Built with CustomTkinter for a stunning, theme-aware interface (light/dark mode support).
- **Configurable**: Save settings in `config.ini` for easy reuse, with adjustable intervals and post limits.
- **Robust Automation**: Runs in a background thread with retry logic for network hiccups.

## Tech Stack 🛠️
- **Python 🐍**: Core language (3.8+).
- **Libraries**:
  - `tweepy` for X API integration.
  - `customtkinter` for the GUI (install via `pip install customtkinter`).
  - `urllib.request` for Reddit scraping.
  - `configparser` for config management.

## Installation 💾
1. Clone the repo:
   ```bash
   git clone https://github.com/kaygaaf/Kayo-MemeMagnet.git

## Beta

I have added a beta version which will be more complex and have more features, but also more prone to bugs and errors.


