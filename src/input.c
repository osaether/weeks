/* input.c - YAML input parser for WEEKS calculator
 * 
 * Reads conductor configuration from YAML files
 * Requires: libyaml (libyaml-dev package on Ubuntu/Debian)
 * 
 * YAML format:
 * frequency: 30e6
 * conductors:
 *   - name: line0
 *     w: 2800e-6
 *     h: 2.0e-6
 *     ...
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <yaml.h>
#include "weeks.h"

/* Global frequency variable */
double global_frequency = 30e6;  /* Default 30 MHz */

/* Helper function to get scalar value from YAML */
static char* get_scalar_value(yaml_event_t *event) {
    if (event->type != YAML_SCALAR_EVENT) {
        return NULL;
    }
    return strdup((char*)event->data.scalar.value);
}

static double safe_atof(const char *str) {
    return str ? atof(str) : 0.0;
}

/* Skip unexpected nested structures */
static int skip_node(yaml_parser_t *parser) {
    yaml_event_t event;
    int depth = 1;
    
    while (depth > 0) {
        if (!yaml_parser_parse(parser, &event)) {
            return 0;
        }
        
        if (event.type == YAML_MAPPING_START_EVENT || event.type == YAML_SEQUENCE_START_EVENT) {
            depth++;
        } else if (event.type == YAML_MAPPING_END_EVENT || event.type == YAML_SEQUENCE_END_EVENT) {
            depth--;
        }
        
        yaml_event_delete(&event);
    }
    
    return 1;
}

/* Parse a conductor from YAML */
static int parse_conductor(yaml_parser_t *parser, conductor *c) {
    yaml_event_t event;
    char *key = NULL;
    int in_mapping = 1;
    
    /* Set defaults */
    c->w = 0.0;
    c->h = 0.0;
    c->x = 0.0;
    c->y = 0.0;
    c->b = 0.5;
    c->nw = 10;
    c->nh = 10;
    c->er = 1.0;
    c->tan_delta = 0.0;
    
    while (in_mapping) {
        if (!yaml_parser_parse(parser, &event)) {
            fprintf(stderr, "YAML parse error\n");
            free(key);
            return 0;
        }
        
        switch (event.type) {
            case YAML_MAPPING_END_EVENT:
                in_mapping = 0;
                break;
                
            case YAML_MAPPING_START_EVENT:
            case YAML_SEQUENCE_START_EVENT:
                skip_node(parser);
                free(key);
                key = NULL;
                break;
                
            case YAML_SCALAR_EVENT:
                if (key == NULL) {
                    /* This is a key */
                    key = get_scalar_value(&event);
                } else {
                    /* This is a value */
                    char *value = get_scalar_value(&event);
                    
                    if (strcmp(key, "name") == 0) {
                        /* Store name if needed */
                    } else if (strcmp(key, "w") == 0) {
                        c->w = safe_atof(value);
                    } else if (strcmp(key, "h") == 0) {
                        c->h = safe_atof(value);
                    } else if (strcmp(key, "x") == 0) {
                        c->x = safe_atof(value);
                    } else if (strcmp(key, "y") == 0) {
                        c->y = safe_atof(value);
                    } else if (strcmp(key, "b") == 0) {
                        c->b = safe_atof(value);
                    } else if (strcmp(key, "nw") == 0) {
                        c->nw = (int)round(safe_atof(value));
                    } else if (strcmp(key, "nh") == 0) {
                        c->nh = (int)round(safe_atof(value));
                    } else if (strcmp(key, "er") == 0) {
                        c->er = safe_atof(value);
                    } else if (strcmp(key, "substrate_h") == 0) {
                        /* Deprecated/ignored: the substrate height is derived
                         * from the conductor geometry (trace-to-ground gap),
                         * not read from the input. */
                        fprintf(stderr, "\n  Note: 'substrate_h' is ignored; "
                                "substrate height is derived from geometry");
                    } else if (strcmp(key, "tan_delta") == 0) {
                        c->tan_delta = safe_atof(value);
                    }
                    
                    free(value);
                    free(key);
                    key = NULL;
                }
                break;
                
            default:
                break;
        }
        
        yaml_event_delete(&event);
    }
    
    free(key);
    
    /* Validate required fields */
    int ok = 1;
    if (c->w <= 0.0) {
        fprintf(stderr, "\n  ERROR: conductor w must be > 0 (got %g)\n", c->w); ok = 0;
    }
    if (c->h <= 0.0) {
        fprintf(stderr, "\n  ERROR: conductor h must be > 0 (got %g)\n", c->h); ok = 0;
    }
    if (c->nw < 1) {
        fprintf(stderr, "\n  ERROR: conductor nw must be >= 1 (got %d)\n", c->nw); ok = 0;
    }
    if (c->nw > 1000) {
        fprintf(stderr, "\n  ERROR: conductor nw must be <= 1000 (got %d)\n", c->nw); ok = 0;
    }
    if (c->nh < 1) {
        fprintf(stderr, "\n  ERROR: conductor nh must be >= 1 (got %d)\n", c->nh); ok = 0;
    }
    if (c->nh > 100) {
        fprintf(stderr, "\n  ERROR: conductor nh must be <= 100 (got %d)\n", c->nh); ok = 0;
    }
    if (c->b <= 0.0 || c->b > 1.0) {
        fprintf(stderr, "\n  ERROR: conductor b must be in (0, 1] (got %g)\n", c->b); ok = 0;
    }
    if (!ok)
        return 0;

    c->n = c->nw * c->nh;

    fprintf(stderr, "\n  Conductor: w=%.2e, h=%.2e, er=%.2f, tan_delta=%.4f",
            c->w, c->h, c->er, c->tan_delta);

    return 1;
}

conductor *getinput(FILE *fp, int *n) {
    yaml_parser_t parser;
    yaml_event_t event;
    conductor *conductors;
    int conductor_count = 0;
    int in_conductors_sequence = 0;
    int top_level_mapping_seen = 0;
    char *key = NULL;
    
    conductors = (conductor *)malloc(sizeof(conductor) * MAX_CONDUCTORS);
    if (conductors == NULL) {
        fprintf(stderr, "Failed to allocate conductor array\n");
        return NULL;
    }

    /* Initialize parser */
    if (!yaml_parser_initialize(&parser)) {
        fprintf(stderr, "Failed to initialize YAML parser\n");
        free(conductors);
        return NULL;
    }
    
    yaml_parser_set_input_file(&parser, fp);
    
    fprintf(stderr, "\nParsing YAML input file...");
    
    /* Parse YAML */
    int done = 0;
    while (!done) {
        if (!yaml_parser_parse(&parser, &event)) {
            fprintf(stderr, "YAML parse error at line %lu\n", parser.problem_mark.line);
            free(key);
            free(conductors);
            yaml_parser_delete(&parser);
            return NULL;
        }
        
        switch (event.type) {
            case YAML_STREAM_END_EVENT:
                done = 1;
                break;
                
            case YAML_SCALAR_EVENT:
                if (!in_conductors_sequence) {
                    if (key == NULL) {
                        key = get_scalar_value(&event);
                    } else {
                        /* Top-level key-value pair */
                        char *value = get_scalar_value(&event);
                        
                        if (strcmp(key, "frequency") == 0) {
                            global_frequency = safe_atof(value);
                            fprintf(stderr, "\nFrequency: %.2e Hz (%.2f MHz)",
                                    global_frequency, global_frequency/1e6);
                        }
                        
                        free(value);
                        free(key);
                        key = NULL;
                    }
                }
                break;
                
            case YAML_SEQUENCE_START_EVENT:
                if (key && strcmp(key, "conductors") == 0) {
                    in_conductors_sequence = 1;
                    free(key);
                    key = NULL;
                } else {
                    skip_node(&parser);
                    free(key);
                    key = NULL;
                }
                break;
                
            case YAML_SEQUENCE_END_EVENT:
                in_conductors_sequence = 0;
                break;
                
            case YAML_MAPPING_START_EVENT:
                if (in_conductors_sequence) {
                    if (conductor_count < MAX_CONDUCTORS) {
                        if (parse_conductor(&parser, &conductors[conductor_count])) {
                            conductor_count++;
                        }
                    } else {
                        fprintf(stderr, "WARNING: conductor limit (%d) reached;"
                                " extra conductors ignored\n", MAX_CONDUCTORS);
                        skip_node(&parser);
                    }
                } else if (!top_level_mapping_seen) {
                    top_level_mapping_seen = 1;
                } else {
                    skip_node(&parser);
                    free(key);
                    key = NULL;
                }
                break;
                
            default:
                break;
        }
        
        yaml_event_delete(&event);
    }
    
    free(key);
    yaml_parser_delete(&parser);

    if (global_frequency <= 0.0) {
        fprintf(stderr, "ERROR: frequency must be > 0 (got %g)\n", global_frequency);
        free(conductors);
        return NULL;
    }

    *n = conductor_count;

    fprintf(stderr, "\n\nTotal conductors loaded: %d\n", conductor_count);

    /* Need at least a ground plane (line0) plus one signal trace. */
    if (conductor_count < 2) {
        fprintf(stderr, "ERROR: need at least 2 conductors (ground plane + "
                        "1 signal trace), but %d were loaded.\n", conductor_count);
        free(conductors);
        return NULL;
    }

    return conductors;
}
