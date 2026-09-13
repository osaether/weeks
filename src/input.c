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
#include <errno.h>
#include <ctype.h>
#include <yaml.h>
#include "weeks.h"

/* Global frequency variable */
double global_frequency = 30e6;  /* Default 30 MHz */

/* libyaml scalars have an explicit length and may contain embedded NULs.
 * Reject those before treating keys or numeric values as C strings. */
static const char *scalar_text(const yaml_node_t *node, const char *field) {
    if (node->type != YAML_SCALAR_NODE ||
        memchr(node->data.scalar.value, '\0', node->data.scalar.length) != NULL) {
        fprintf(stderr, "ERROR: %s must be a scalar without NUL characters\n", field);
        return NULL;
    }
    return (const char *)node->data.scalar.value;
}

/* Validate only model mappings; unknown metadata values remain opaque. */
static int validate_mapping(yaml_document_t *document, yaml_node_t *node,
                            const char *context) {
    yaml_node_pair_t *pair, *previous;
    if (node == NULL || node->type != YAML_MAPPING_NODE) {
        fprintf(stderr, "ERROR: %s must be a mapping\n", context);
        return 0;
    }
    for (pair = node->data.mapping.pairs.start;
         pair < node->data.mapping.pairs.top; pair++) {
        const char *key = scalar_text(yaml_document_get_node(document, pair->key), "key");
        if (key == NULL)
            return 0;
        /* The document loader resolves aliases, but does not apply YAML merge
         * keys. Ignoring one could silently discard material/mesh settings. */
        if (strcmp(key, "<<") == 0) {
            fprintf(stderr, "ERROR: YAML merge keys (<<) are not supported in %s; "
                            "use explicit fields or a direct alias\n", context);
            return 0;
        }
        for (previous = node->data.mapping.pairs.start; previous < pair; previous++) {
            yaml_node_t *old_key = yaml_document_get_node(document, previous->key);
            if (strcmp(key, (const char *)old_key->data.scalar.value) == 0) {
                fprintf(stderr, "ERROR: duplicate key '%s' in %s\n", key, context);
                return 0;
            }
        }
    }
    return 1;
}

static int parse_number(const char *key, const yaml_node_t *node, double *result) {
    const char *str = scalar_text(node, key);
    char *end;
    double value;

    if (str == NULL)
        return 0;
    errno = 0;
    value = strtod(str, &end);
    if (end == str)
        goto invalid;
    while (isspace((unsigned char)*end))
        end++;
    if (*end != '\0' || errno == ERANGE || !isfinite(value))
        goto invalid;
    *result = value;
    return 1;

invalid:
    fprintf(stderr, "\n  ERROR: %s must be a finite number (got '%s')\n", key, str);
    return 0;
}

static int parse_conductor_value(conductor *c, const char *key, const yaml_node_t *value) {
    double *field = NULL;
    if (strcmp(key, "w") == 0) field = &c->w;
    else if (strcmp(key, "h") == 0) field = &c->h;
    else if (strcmp(key, "x") == 0) field = &c->x;
    else if (strcmp(key, "y") == 0) field = &c->y;
    else if (strcmp(key, "b") == 0) field = &c->b;
    else if (strcmp(key, "er") == 0) field = &c->er;
    else if (strcmp(key, "tan_delta") == 0) field = &c->tan_delta;

    if (field != NULL)
        return parse_number(key, value, field);

    if (strcmp(key, "nw") == 0 || strcmp(key, "nh") == 0) {
        double divisions;
        int width = strcmp(key, "nw") == 0;
        int limit = width ? 1000 : 100;
        if (!parse_number(key, value, &divisions))
            return 0;
        /* Check before converting to int to avoid out-of-range casts. */
        if (divisions < 1 || divisions > limit || trunc(divisions) != divisions) {
            fprintf(stderr, "\n  ERROR: %s must be an integer in [1, %d] (got '%s')\n",
                    key, limit, (const char *)value->data.scalar.value);
            return 0;
        }
        if (width) c->nw = (int)divisions;
        else c->nh = (int)divisions;
    } else if (strcmp(key, "substrate_h") == 0) {
        fprintf(stderr, "\n  Note: 'substrate_h' is ignored; "
                "substrate height is derived from geometry");
    }
    /* Names and unknown fields do not affect the calculation. */
    return 1;
}

/* Parse a conductor from YAML */
static int parse_conductor(yaml_document_t *document, yaml_node_t *node, conductor *c) {
    yaml_node_pair_t *pair;

    if (!validate_mapping(document, node, "conductor"))
        return 0;
    
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
    
    for (pair = node->data.mapping.pairs.start;
         pair < node->data.mapping.pairs.top; pair++) {
        yaml_node_t *key = yaml_document_get_node(document, pair->key);
        yaml_node_t *value = yaml_document_get_node(document, pair->value);
        if (!parse_conductor_value(c, (const char *)key->data.scalar.value, value))
            return 0;
    }
    
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
    if (c->er < 1.0) {
        fprintf(stderr, "\n  ERROR: conductor er must be >= 1 (got %g)\n", c->er); ok = 0;
    }
    if (c->tan_delta < 0.0) {
        fprintf(stderr, "\n  ERROR: conductor tan_delta must be >= 0 (got %g)\n", c->tan_delta); ok = 0;
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
    yaml_document_t document, trailing;
    yaml_node_t *root, *sequence = NULL;
    yaml_node_pair_t *pair;
    yaml_node_item_t *item;
    conductor *conductors = NULL;
    int conductor_count = 0;
    double frequency = 30e6;

    *n = 0;

    /* Initialize parser */
    if (!yaml_parser_initialize(&parser)) {
        fprintf(stderr, "Failed to initialize YAML parser\n");
        return NULL;
    }
    
    yaml_parser_set_input_file(&parser, fp);
    
    fprintf(stderr, "\nParsing YAML input file...");
    
    /* Load a document so keys and values cannot become desynchronized by
     * collections or aliases. libyaml resolves aliases to document nodes. */
    if (!yaml_parser_load(&parser, &document)) {
        fprintf(stderr, "YAML parse error at line %zu: %s\n",
                parser.problem_mark.line + 1, parser.problem);
        yaml_parser_delete(&parser);
        return NULL;
    }

    root = yaml_document_get_root_node(&document);
    if (!validate_mapping(&document, root, "input root"))
        goto input_error;

    /* Consume the stream end as well: a second document or malformed trailing
     * input must never be silently ignored. */
    if (!yaml_parser_load(&parser, &trailing)) {
        fprintf(stderr, "YAML parse error at line %zu: %s\n",
                parser.problem_mark.line + 1, parser.problem);
        goto input_error;
    }
    int has_trailing_document = yaml_document_get_root_node(&trailing) != NULL;
    yaml_document_delete(&trailing);
    if (has_trailing_document) {
        fprintf(stderr, "ERROR: input must contain exactly one YAML document\n");
        goto input_error;
    }

    for (pair = root->data.mapping.pairs.start;
         pair < root->data.mapping.pairs.top; pair++) {
        yaml_node_t *key_node = yaml_document_get_node(&document, pair->key);
        const char *key = (const char *)key_node->data.scalar.value;
        yaml_node_t *value = yaml_document_get_node(&document, pair->value);
        if (strcmp(key, "frequency") == 0) {
            if (!parse_number(key, value, &frequency))
                goto input_error;
        } else if (strcmp(key, "conductors") == 0) {
            sequence = value;
        }
    }

    if (frequency <= 0.0) {
        fprintf(stderr, "ERROR: frequency must be > 0 (got %g)\n", frequency);
        goto input_error;
    }
    if (sequence == NULL || sequence->type != YAML_SEQUENCE_NODE) {
        fprintf(stderr, "ERROR: conductors must be a sequence of mappings\n");
        goto input_error;
    }
    size_t count = sequence->data.sequence.items.top - sequence->data.sequence.items.start;
    if (count > MAX_CONDUCTORS) {
        fprintf(stderr, "ERROR: at most %d conductors are supported (got %zu); "
                        "no conductors were loaded\n", MAX_CONDUCTORS, count);
        goto input_error;
    }

    /* Need at least a ground plane (line0) plus one signal trace. */
    if (count < 2) {
        fprintf(stderr, "ERROR: need at least 2 conductors (ground plane + "
                        "1 signal trace), but %zu were supplied.\n", count);
        goto input_error;
    }

    conductors = malloc(sizeof(conductor) * count);
    if (conductors == NULL) {
        fprintf(stderr, "Failed to allocate conductor array\n");
        goto input_error;
    }
    for (item = sequence->data.sequence.items.start;
         item < sequence->data.sequence.items.top; item++) {
        if (!parse_conductor(&document, yaml_document_get_node(&document, *item),
                             &conductors[conductor_count]))
            goto input_error;
        conductor_count++;
    }

    global_frequency = frequency;
    *n = conductor_count;
    fprintf(stderr, "\nFrequency: %.2e Hz (%.2f MHz)", frequency, frequency/1e6);
    fprintf(stderr, "\n\nTotal conductors loaded: %d\n", conductor_count);
    yaml_document_delete(&document);
    yaml_parser_delete(&parser);
    return conductors;

input_error:
    free(conductors);
    yaml_document_delete(&document);
    yaml_parser_delete(&parser);
    return NULL;
}
