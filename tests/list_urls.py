import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kooptimizer.settings')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def show_urls(lis, acc=''):
    for entry in lis:
        if isinstance(entry, URLPattern):
            print(f"  {acc}{entry.pattern}")
        elif isinstance(entry, URLResolver):
            show_urls(entry.url_patterns, acc + str(entry.pattern))

print("\n" + "="*70)
print("  ALL URLS IN YOUR KOOPTIMIZER APPLICATION")
print("="*70 + "\n")

print("🌐 PUBLIC URLS (No login required):")
print("-" * 70)
public_urls = [
    "/",
    "/login/",
    "/about/",
    "/download/",
    "/users/logout/",
    "/static/* (all static files)",
    "/admin/* (Django admin)"
]
for url in public_urls:
    print(f"  ✅ {url}")

print("\n🔒 PROTECTED URLS (Login required):")
print("-" * 70)

resolver = get_resolver()
show_urls(resolver.url_patterns)

print("\n" + "="*70)
print("\nTo test: Logout first, then try accessing any protected URL")
print("="*70 + "\n")
