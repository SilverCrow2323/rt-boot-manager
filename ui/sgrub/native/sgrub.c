/*
 * SGRUB native preview renderer.
 *
 * SDL2 only: no X11, Wayland, SDL_ttf, SDL_image or Python runtime required.
 * This build is a profile browser. It deliberately does not reboot, chain-load,
 * write boot state, touch block devices or modify the boot chain.
 */

#include <SDL.h>
#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SCREEN_W 640
#define SCREEN_H 480
#define SGRUB_VERSION "0.1.0-preview"

typedef struct {
    const char *id;
    const char *name;
    const char *version;
    const char *status;
    const char *boot_mode;
    bool needs_hardware_check;
} SgrubProfile;

#include "profiles.generated.h"

typedef struct {
    int selected;
    int default_index;
    bool details;
    bool running;
    bool input_dump;
    char last_input[40];
} UiState;

typedef struct {
    Uint8 r, g, b, a;
} Rgb;

static const Rgb C_BG       = {  7,  11,  17, 255};
static const Rgb C_PANEL    = { 15,  23,  33, 255};
static const Rgb C_PANEL_HI = { 22,  37,  49, 255};
static const Rgb C_PANEL_2  = { 11,  18,  27, 255};
static const Rgb C_LINE     = { 38,  53,  66, 255};
static const Rgb C_TEXT     = {235, 242, 246, 255};
static const Rgb C_MUTED    = {132, 151, 164, 255};
static const Rgb C_ACCENT   = {183, 243,  91, 255};
static const Rgb C_CYAN     = { 80, 214, 195, 255};
static const Rgb C_ORANGE   = {255, 181,  83, 255};
static const Rgb C_RED      = {242, 101, 110, 255};

/* Compact 5x7 font. Each row uses its five low bits. */
static const char FONT_CHARS[] = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.:/()!?+><_%";
static const Uint8 FONT_ROWS[][7] = {
    { 0,  0,  0,  0,  0,  0,  0}, /* space */
    {14, 17, 17, 31, 17, 17, 17}, /* A */
    {30, 17, 17, 30, 17, 17, 30}, /* B */
    {14, 17, 16, 16, 16, 17, 14}, /* C */
    {30, 17, 17, 17, 17, 17, 30}, /* D */
    {31, 16, 16, 30, 16, 16, 31}, /* E */
    {31, 16, 16, 30, 16, 16, 16}, /* F */
    {14, 17, 16, 23, 17, 17, 15}, /* G */
    {17, 17, 17, 31, 17, 17, 17}, /* H */
    {14,  4,  4,  4,  4,  4, 14}, /* I */
    { 7,  2,  2,  2, 18, 18, 12}, /* J */
    {17, 18, 20, 24, 20, 18, 17}, /* K */
    {16, 16, 16, 16, 16, 16, 31}, /* L */
    {17, 27, 21, 21, 17, 17, 17}, /* M */
    {17, 25, 21, 19, 17, 17, 17}, /* N */
    {14, 17, 17, 17, 17, 17, 14}, /* O */
    {30, 17, 17, 30, 16, 16, 16}, /* P */
    {14, 17, 17, 17, 21, 18, 13}, /* Q */
    {30, 17, 17, 30, 20, 18, 17}, /* R */
    {15, 16, 16, 14,  1,  1, 30}, /* S */
    {31,  4,  4,  4,  4,  4,  4}, /* T */
    {17, 17, 17, 17, 17, 17, 14}, /* U */
    {17, 17, 17, 17, 17, 10,  4}, /* V */
    {17, 17, 17, 21, 21, 21, 10}, /* W */
    {17, 17, 10,  4, 10, 17, 17}, /* X */
    {17, 17, 10,  4,  4,  4,  4}, /* Y */
    {31,  1,  2,  4,  8, 16, 31}, /* Z */
    {14, 17, 19, 21, 25, 17, 14}, /* 0 */
    { 4, 12,  4,  4,  4,  4, 14}, /* 1 */
    {14, 17,  1,  2,  4,  8, 31}, /* 2 */
    {30,  1,  1, 14,  1,  1, 30}, /* 3 */
    { 2,  6, 10, 18, 31,  2,  2}, /* 4 */
    {31, 16, 16, 30,  1,  1, 30}, /* 5 */
    {14, 16, 16, 30, 17, 17, 14}, /* 6 */
    {31,  1,  2,  4,  8,  8,  8}, /* 7 */
    {14, 17, 17, 14, 17, 17, 14}, /* 8 */
    {14, 17, 17, 15,  1,  1, 14}, /* 9 */
    { 0,  0,  0, 31,  0,  0,  0}, /* - */
    { 0,  0,  0,  0,  0, 12, 12}, /* . */
    { 0, 12, 12,  0, 12, 12,  0}, /* : */
    { 1,  2,  2,  4,  8,  8, 16}, /* / */
    { 2,  4,  8,  8,  8,  4,  2}, /* ( */
    { 8,  4,  2,  2,  2,  4,  8}, /* ) */
    { 4,  4,  4,  4,  4,  0,  4}, /* ! */
    {14, 17,  1,  2,  4,  0,  4}, /* ? */
    { 0,  4,  4, 31,  4,  4,  0}, /* + */
    {16,  8,  4,  2,  4,  8, 16}, /* > */
    { 1,  2,  4,  8,  4,  2,  1}, /* < */
    { 0,  0,  0,  0,  0,  0, 31}, /* _ */
    {17,  2,  4,  8, 17,  0,  0}  /* % */
};

enum Action {
    ACTION_UP,
    ACTION_DOWN,
    ACTION_LEFT,
    ACTION_RIGHT,
    ACTION_ACCEPT,
    ACTION_BACK,
    ACTION_DEFAULT
};

static void set_color(SDL_Renderer *renderer, Rgb color)
{
    SDL_SetRenderDrawColor(renderer, color.r, color.g, color.b, color.a);
}

static void rect(SDL_Renderer *renderer, int x, int y, int w, int h, Rgb color)
{
    SDL_Rect area = {x, y, w, h};
    set_color(renderer, color);
    SDL_RenderFillRect(renderer, &area);
}

static void outline(SDL_Renderer *renderer, int x, int y, int w, int h, Rgb color)
{
    SDL_Rect area = {x, y, w, h};
    set_color(renderer, color);
    SDL_RenderDrawRect(renderer, &area);
}

static void hline(SDL_Renderer *renderer, int x1, int x2, int y, Rgb color)
{
    set_color(renderer, color);
    SDL_RenderDrawLine(renderer, x1, y, x2, y);
}

static int glyph_index(char ch)
{
    const char *found;
    ch = (char)toupper((unsigned char)ch);
    found = strchr(FONT_CHARS, ch);
    return found ? (int)(found - FONT_CHARS) : 0;
}

static int draw_text(SDL_Renderer *renderer, int x, int y, const char *text,
                     int scale, Rgb color)
{
    int origin_x = x;
    if (scale < 1) {
        scale = 1;
    }

    set_color(renderer, color);
    for (const char *cursor = text; *cursor; ++cursor) {
        int index = glyph_index(*cursor);
        for (int row = 0; row < 7; ++row) {
            for (int col = 0; col < 5; ++col) {
                if ((FONT_ROWS[index][row] & (1u << (4 - col))) != 0u) {
                    SDL_Rect pixel = {
                        x + col * scale, y + row * scale, scale, scale
                    };
                    SDL_RenderFillRect(renderer, &pixel);
                }
            }
        }
        x += 6 * scale;
        if (x > SCREEN_W + 8) {
            break;
        }
    }
    return x - origin_x;
}

static void draw_chip(SDL_Renderer *renderer, int x, int y, int w,
                      const char *label, Rgb fill, Rgb ink)
{
    rect(renderer, x, y, w, 20, fill);
    draw_text(renderer, x + 7, y + 6, label, 1, ink);
}

static void draw_header(SDL_Renderer *renderer)
{
    rect(renderer, 28, 23, 42, 42, C_ACCENT);
    draw_text(renderer, 34, 35, "RT", 2, C_BG);
    draw_text(renderer, 84, 24, "RT BOOT MANAGER", 2, C_TEXT);
    draw_text(renderer, 84, 52, "SPDW FACTORY / SGRUB", 1, C_MUTED);
    draw_chip(renderer, 448, 27, 164, "H700 / PREVIEW", C_PANEL_HI, C_CYAN);
    hline(renderer, 28, 612, 82, C_LINE);
}

static void draw_profile_card(SDL_Renderer *renderer, int index, int y,
                              const UiState *state)
{
    const SgrubProfile *profile = &SGRUB_PROFILES[index];
    bool selected = index == state->selected;
    bool is_default = index == state->default_index;
    Rgb background = selected ? C_PANEL_HI : C_PANEL;

    rect(renderer, 28, y, 370, 84, background);
    outline(renderer, 28, y, 370, 84, selected ? C_ACCENT : C_LINE);
    rect(renderer, 40, y + 17, 48, 48, C_PANEL_2);
    if (selected) {
        rect(renderer, 40, y + 17, 3, 48, C_ACCENT);
    }
    draw_text(renderer, 54, y + 34, profile->id, 2, selected ? C_ACCENT : C_CYAN);
    draw_text(renderer, 102, y + 19, profile->name, 2, C_TEXT);
    draw_text(renderer, 102, y + 49, profile->version, 1, C_MUTED);

    if (is_default) {
        draw_chip(renderer, 310, y + 16, 76, "DEFAULT", C_ACCENT, C_BG);
    } else if (selected) {
        draw_chip(renderer, 310, y + 16, 76, "SELECTED", C_PANEL_2, C_CYAN);
    }
    if (profile->needs_hardware_check) {
        draw_text(renderer, 310, y + 57, "VERIFY HW", 1, C_ORANGE);
    }
}

static void draw_selected_panel(SDL_Renderer *renderer, const UiState *state,
                                bool controller_connected)
{
    const SgrubProfile *profile = &SGRUB_PROFILES[state->selected];
    rect(renderer, 414, 120, 198, 278, C_PANEL);
    outline(renderer, 414, 120, 198, 278, C_LINE);
    draw_text(renderer, 430, 137, "PROFILE INFO", 1, C_CYAN);
    draw_text(renderer, 430, 160, profile->name, 2, C_TEXT);
    hline(renderer, 430, 596, 185, C_LINE);

    draw_text(renderer, 430, 201, "RELEASE", 1, C_MUTED);
    draw_text(renderer, 430, 215, profile->version, 1, C_TEXT);

    draw_text(renderer, 430, 244, "BOOT PATH", 1, C_MUTED);
    draw_text(renderer, 430, 258, profile->boot_mode, 1, C_TEXT);

    draw_text(renderer, 430, 287, "HARDWARE", 1, C_MUTED);
    draw_text(renderer, 430, 301,
              profile->needs_hardware_check ? "RAM / DTB CHECK" : "BOARD CHECK",
              1, C_ORANGE);

    hline(renderer, 430, 596, 326, C_LINE);
    draw_text(renderer, 430, 342, "BOOT HANDOFF", 1, C_MUTED);
    draw_text(renderer, 430, 358, "NOT CONNECTED", 1, C_RED);
    draw_text(renderer, 430, 378, controller_connected ? "PAD CONNECTED" : "KEYBOARD READY",
              1, controller_connected ? C_CYAN : C_MUTED);
}

static void draw_detail_screen(SDL_Renderer *renderer, const UiState *state,
                               bool controller_connected)
{
    const SgrubProfile *profile = &SGRUB_PROFILES[state->selected];
    rect(renderer, 28, 108, 584, 292, C_PANEL);
    outline(renderer, 28, 108, 584, 292, C_LINE);

    draw_text(renderer, 50, 132, "PROFILE DETAILS", 1, C_CYAN);
    draw_text(renderer, 50, 160, profile->name, 3, C_TEXT);
    draw_text(renderer, 50, 205, "VERSION", 1, C_MUTED);
    draw_text(renderer, 50, 222, profile->version, 2, C_ACCENT);

    draw_text(renderer, 50, 266, "BOOT PATH", 1, C_MUTED);
    draw_text(renderer, 50, 283, profile->boot_mode, 2, C_TEXT);

    rect(renderer, 350, 136, 236, 222, C_PANEL_2);
    outline(renderer, 350, 136, 236, 222, C_LINE);
    draw_text(renderer, 368, 155, "SAFETY STATE", 1, C_CYAN);
    draw_text(renderer, 368, 184, "PREVIEW ONLY", 2, C_ACCENT);
    hline(renderer, 368, 568, 209, C_LINE);
    draw_text(renderer, 368, 227, "NO BOOT ACTION", 1, C_RED);
    draw_text(renderer, 368, 244, "NO REBOOT OR", 1, C_MUTED);
    draw_text(renderer, 368, 257, "KERNEL SWITCH", 1, C_MUTED);
    draw_text(renderer, 368, 284, "HARDWARE CHECK", 1, C_ORANGE);
    draw_text(renderer, 368, 301,
              profile->needs_hardware_check ? "RAM + PANEL DTB" : "BOARD + PANEL",
              1, C_TEXT);
    draw_text(renderer, 368, 330,
              controller_connected ? "PAD CONNECTED" : "KEYBOARD READY",
              1, C_CYAN);
    draw_text(renderer, 50, 343, "THIS BUILD DOES NOT CHANGE BOOT STATE.", 1, C_MUTED);
}

static void draw_footer(SDL_Renderer *renderer, const UiState *state)
{
    hline(renderer, 28, 612, 420, C_LINE);
    if (state->details) {
        draw_text(renderer, 30, 441, "A OR B  BACK TO PROFILES", 1, C_TEXT);
        draw_text(renderer, 333, 441, "Y  SET SESSION DEFAULT", 1, C_ACCENT);
    } else {
        draw_text(renderer, 30, 441, "DPAD  MOVE", 1, C_TEXT);
        draw_text(renderer, 160, 441, "A  DETAILS", 1, C_CYAN);
        draw_text(renderer, 292, 441, "B  EXIT", 1, C_TEXT);
        draw_text(renderer, 398, 441, "Y  SET DEFAULT", 1, C_ACCENT);
    }
    draw_text(renderer, 30, 461, "NO AUTOSTART  /  NO STORAGE WRITES  /  NO BOOTLOADER CHANGES",
              1, C_MUTED);
    if (state->input_dump && state->last_input[0] != '\0') {
        draw_text(renderer, 455, 461, state->last_input, 1, C_ORANGE);
    }
}

static void render(SDL_Renderer *renderer, const UiState *state,
                   bool controller_connected)
{
    rect(renderer, 0, 0, SCREEN_W, SCREEN_H, C_BG);
    draw_header(renderer);

    if (state->details) {
        draw_detail_screen(renderer, state, controller_connected);
    } else {
        draw_text(renderer, 28, 101, "SYSTEM PROFILES", 1, C_MUTED);
        draw_profile_card(renderer, 0, 120, state);
        if (SGRUB_PROFILE_COUNT > 1) {
            draw_profile_card(renderer, 1, 213, state);
        }
        if (SGRUB_PROFILE_COUNT > 2) {
            draw_profile_card(renderer, 2, 306, state);
        }
        draw_selected_panel(renderer, state, controller_connected);
    }
    draw_footer(renderer, state);
    SDL_RenderPresent(renderer);
}

static void act(UiState *state, enum Action action)
{
    if (state->details) {
        if (action == ACTION_ACCEPT || action == ACTION_BACK) {
            state->details = false;
        } else if (action == ACTION_DEFAULT) {
            state->default_index = state->selected;
            state->details = false;
        }
        return;
    }

    switch (action) {
    case ACTION_UP:
    case ACTION_LEFT:
        state->selected = (state->selected + (int)SGRUB_PROFILE_COUNT - 1)
                          % (int)SGRUB_PROFILE_COUNT;
        break;
    case ACTION_DOWN:
    case ACTION_RIGHT:
        state->selected = (state->selected + 1) % (int)SGRUB_PROFILE_COUNT;
        break;
    case ACTION_ACCEPT:
        state->details = true;
        break;
    case ACTION_BACK:
        state->running = false;
        break;
    case ACTION_DEFAULT:
        state->default_index = state->selected;
        break;
    }
}

static void record_raw_button(UiState *state, Uint8 button)
{
    if (!state->input_dump) {
        return;
    }
    (void)snprintf(state->last_input, sizeof(state->last_input), "RAW BTN %u",
                   (unsigned int)button);
    (void)printf("SGRUB_INPUT raw_button=%u\n", (unsigned int)button);
    (void)fflush(stdout);
}

static int configured_button(const char *variable)
{
    const char *value = getenv(variable);
    char *end = NULL;
    long parsed;
    if (!value || value[0] == '\0') {
        return -1;
    }
    parsed = strtol(value, &end, 10);
    if (!end || *end != '\0' || parsed < 0 || parsed > 255) {
        return -1;
    }
    return (int)parsed;
}

static void handle_raw_button(UiState *state, Uint8 button)
{
    int mapped;
    record_raw_button(state, button);

    mapped = configured_button("RTBM_RAW_A_BUTTON");
    if (mapped >= 0 && button == (Uint8)mapped) {
        act(state, ACTION_ACCEPT);
        return;
    }
    mapped = configured_button("RTBM_RAW_B_BUTTON");
    if (mapped >= 0 && button == (Uint8)mapped) {
        act(state, ACTION_BACK);
        return;
    }
    mapped = configured_button("RTBM_RAW_Y_BUTTON");
    if (mapped >= 0 && button == (Uint8)mapped) {
        act(state, ACTION_DEFAULT);
        return;
    }
    mapped = configured_button("RTBM_RAW_L1_BUTTON");
    if (mapped >= 0 && button == (Uint8)mapped) {
        act(state, ACTION_LEFT);
        return;
    }
    mapped = configured_button("RTBM_RAW_R1_BUTTON");
    if (mapped >= 0 && button == (Uint8)mapped) {
        act(state, ACTION_RIGHT);
    }
}

static bool open_first_controller(SDL_GameController **controller)
{
    int count = SDL_NumJoysticks();
    for (int i = 0; i < count; ++i) {
        if (SDL_IsGameController(i)) {
            *controller = SDL_GameControllerOpen(i);
            if (*controller) {
                return true;
            }
        }
    }
    return false;
}

static SDL_Joystick *open_first_raw_joystick(void)
{
    int count = SDL_NumJoysticks();
    for (int i = 0; i < count; ++i) {
        if (!SDL_IsGameController(i)) {
            SDL_Joystick *joystick = SDL_JoystickOpen(i);
            if (joystick) {
                return joystick;
            }
        }
    }
    return NULL;
}

static void handle_controller_button(UiState *state, Uint8 button)
{
    switch (button) {
    case SDL_CONTROLLER_BUTTON_DPAD_UP:        act(state, ACTION_UP); break;
    case SDL_CONTROLLER_BUTTON_DPAD_DOWN:      act(state, ACTION_DOWN); break;
    case SDL_CONTROLLER_BUTTON_DPAD_LEFT:      act(state, ACTION_LEFT); break;
    case SDL_CONTROLLER_BUTTON_DPAD_RIGHT:     act(state, ACTION_RIGHT); break;
    case SDL_CONTROLLER_BUTTON_LEFTSHOULDER:   act(state, ACTION_LEFT); break;
    case SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:  act(state, ACTION_RIGHT); break;
    case SDL_CONTROLLER_BUTTON_A:              act(state, ACTION_ACCEPT); break;
    case SDL_CONTROLLER_BUTTON_B:              act(state, ACTION_BACK); break;
    case SDL_CONTROLLER_BUTTON_Y:              act(state, ACTION_DEFAULT); break;
    default: break;
    }
}

static void usage(const char *program)
{
    (void)printf(
        "Rt:BOOT MANAGER / SGRUB %s\n"
        "Usage: %s [--fullscreen] [--input-dump] [--self-test] [--version]\n"
        "\n"
        "This preview browses profiles only. It does not boot, reboot or write storage.\n"
        "Raw joystick button mappings may be supplied with RTBM_RAW_*_BUTTON variables.\n",
        SGRUB_VERSION, program);
}

int main(int argc, char **argv)
{
    bool fullscreen = false;
    bool input_dump = false;
    bool controller_connected;
    SDL_Window *window = NULL;
    SDL_Renderer *renderer = NULL;
    SDL_GameController *controller = NULL;
    SDL_Joystick *raw_joystick = NULL;
    UiState state = {0, 0, false, true, false, {0}};

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--fullscreen") == 0) {
            fullscreen = true;
        } else if (strcmp(argv[i], "--windowed") == 0) {
            fullscreen = false;
        } else if (strcmp(argv[i], "--input-dump") == 0) {
            input_dump = true;
        } else if (strcmp(argv[i], "--self-test") == 0) {
            (void)printf("SGRUB self-test: %lu profiles\n",
                         (unsigned long)SGRUB_PROFILE_COUNT);
            for (size_t p = 0; p < SGRUB_PROFILE_COUNT; ++p) {
                (void)printf("%s\t%s\t%s\n", SGRUB_PROFILES[p].id,
                             SGRUB_PROFILES[p].name, SGRUB_PROFILES[p].version);
            }
            return 0;
        } else if (strcmp(argv[i], "--version") == 0) {
            (void)printf("%s\n", SGRUB_VERSION);
            return 0;
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            usage(argv[0]);
            return 0;
        } else {
            (void)fprintf(stderr, "Unknown option: %s\n", argv[i]);
            usage(argv[0]);
            return 2;
        }
    }
    state.input_dump = input_dump;

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMECONTROLLER |
                 SDL_INIT_JOYSTICK | SDL_INIT_EVENTS) != 0) {
        (void)fprintf(stderr, "SGRUB: SDL_Init failed: %s\n", SDL_GetError());
        return 1;
    }

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "1");
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1");
    SDL_GameControllerEventState(SDL_ENABLE);
    SDL_JoystickEventState(SDL_ENABLE);

    Uint32 window_flags = SDL_WINDOW_SHOWN;
    if (fullscreen) {
        window_flags |= SDL_WINDOW_FULLSCREEN_DESKTOP;
    }
    window = SDL_CreateWindow("Rt:BOOT MANAGER / SGRUB",
                              SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              SCREEN_W, SCREEN_H, window_flags);
    if (!window) {
        (void)fprintf(stderr, "SGRUB: cannot create window: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    /* Software rendering avoids requiring EGL/OpenGL on the framebuffer path. */
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_SOFTWARE);
    if (!renderer) {
        (void)fprintf(stderr, "SGRUB: cannot create SDL renderer: %s\n", SDL_GetError());
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    (void)SDL_RenderSetLogicalSize(renderer, SCREEN_W, SCREEN_H);
    (void)SDL_RenderSetIntegerScale(renderer, SDL_FALSE);
    SDL_ShowCursor(SDL_DISABLE);

    controller_connected = open_first_controller(&controller);
    if (!controller_connected) {
        raw_joystick = open_first_raw_joystick();
        controller_connected = raw_joystick != NULL;
    }

    while (state.running) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
            case SDL_QUIT:
                state.running = false;
                break;
            case SDL_KEYDOWN:
                if (event.key.repeat != 0) {
                    break;
                }
                switch (event.key.keysym.sym) {
                case SDLK_UP:       act(&state, ACTION_UP); break;
                case SDLK_DOWN:     act(&state, ACTION_DOWN); break;
                case SDLK_LEFT:     act(&state, ACTION_LEFT); break;
                case SDLK_RIGHT:    act(&state, ACTION_RIGHT); break;
                case SDLK_RETURN:
                case SDLK_SPACE:    act(&state, ACTION_ACCEPT); break;
                case SDLK_ESCAPE:
                case SDLK_BACKSPACE: act(&state, ACTION_BACK); break;
                case SDLK_y:        act(&state, ACTION_DEFAULT); break;
                default: break;
                }
                break;
            case SDL_CONTROLLERBUTTONDOWN:
                handle_controller_button(&state, event.cbutton.button);
                break;
            case SDL_CONTROLLERDEVICEADDED:
                if (!controller) {
                    controller = SDL_GameControllerOpen(event.cdevice.which);
                    if (controller) {
                        if (raw_joystick) {
                            SDL_JoystickClose(raw_joystick);
                            raw_joystick = NULL;
                        }
                        controller_connected = true;
                    }
                }
                break;
            case SDL_CONTROLLERDEVICEREMOVED:
                if (controller &&
                    SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(controller)) ==
                    event.cdevice.which) {
                    SDL_GameControllerClose(controller);
                    controller = NULL;
                    controller_connected = false;
                }
                break;
            case SDL_JOYHATMOTION:
                if (event.jhat.value & SDL_HAT_UP) {
                    act(&state, ACTION_UP);
                } else if (event.jhat.value & SDL_HAT_DOWN) {
                    act(&state, ACTION_DOWN);
                } else if (event.jhat.value & SDL_HAT_LEFT) {
                    act(&state, ACTION_LEFT);
                } else if (event.jhat.value & SDL_HAT_RIGHT) {
                    act(&state, ACTION_RIGHT);
                }
                break;
            case SDL_JOYBUTTONDOWN:
                handle_raw_button(&state, event.jbutton.button);
                break;
            case SDL_JOYDEVICEADDED:
                if (!controller && !raw_joystick) {
                    raw_joystick = SDL_JoystickOpen(event.jdevice.which);
                    if (raw_joystick) {
                        controller_connected = true;
                    }
                }
                break;
            case SDL_JOYDEVICEREMOVED:
                if (raw_joystick &&
                    SDL_JoystickInstanceID(raw_joystick) == event.jdevice.which) {
                    SDL_JoystickClose(raw_joystick);
                    raw_joystick = NULL;
                    controller_connected = false;
                }
                break;
            default:
                break;
            }
        }

        render(renderer, &state, controller_connected);
        SDL_Delay(16);
    }

    if (controller) {
        SDL_GameControllerClose(controller);
    }
    if (raw_joystick) {
        SDL_JoystickClose(raw_joystick);
    }
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return 0;
}
