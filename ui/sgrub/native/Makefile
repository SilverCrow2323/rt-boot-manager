CC ?= cc
PKG_CONFIG ?= pkg-config
TARGET ?= build/sgrub
SDL_CFLAGS ?= $(shell $(PKG_CONFIG) --cflags sdl2 2>/dev/null)
SDL_LIBS ?= $(shell $(PKG_CONFIG) --libs sdl2 2>/dev/null)
CPPFLAGS ?=
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
LDFLAGS ?=

.PHONY: all clean check-sdl self-test

all: check-sdl $(TARGET)

check-sdl:
	@$(PKG_CONFIG) --exists sdl2 || { echo "SDL2 development files were not found (pkg-config sdl2)." >&2; exit 1; }

$(TARGET): sgrub.c profiles.generated.h
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SDL_CFLAGS) -I. sgrub.c -o $@ $(LDFLAGS) $(SDL_LIBS)

self-test: $(TARGET)
	$(TARGET) --self-test

clean:
	rm -rf build
