#!/usr/bin/env python
"""
Generate a new Django SECRET_KEY for production use.

Usage:
    python generate_secret_key.py

This will print a new random SECRET_KEY that you can copy to your .env file.
"""

from django.core.management.utils import get_random_secret_key

if __name__ == '__main__':
    secret_key = get_random_secret_key()
    print("\n" + "="*70)
    print("  NEW SECRET KEY GENERATED")
    print("="*70)
    print(f"\n{secret_key}\n")
    print("="*70)
    print("Copy the above key and add it to your .env file:")
    print("SECRET_KEY=" + secret_key)
    print("="*70 + "\n")
    print("⚠️  IMPORTANT: Keep this secret and never commit it to git!")
    print("\n")
