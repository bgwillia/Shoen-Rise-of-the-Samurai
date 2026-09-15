# Final replay measurements

All values are milliseconds, median / worst. Thirty repetitions per listed action; source is replay. Input-to-logic is unavailable. Actual cancellation scenes contain N+1 buildings. Render endpoint: matching backbuffer ready on RT.

## 1 initial buildings

| Interaction | Input → logic | Logic | Logic → backbuffer | Total replay → backbuffer |
|---|---:|---:|---:|---:|
| select | N/A | 0.029 / 0.036 | 15.552 / 16.084 | 15.583 / 16.113 |
| clear | N/A | 0.015 / 0.018 | 15.525 / 16.552 | 15.539 / 16.567 |
| switch | N/A | N/A | N/A | N/A |
| enter | N/A | 0.012 / 0.014 | 15.500 / 16.701 | 15.513 / 16.714 |
| rotate | N/A | 0.049 / 0.082 | 15.647 / 16.615 | 15.693 / 16.660 |
| place_success | N/A | 0.071 / 0.099 | 23.681 / 24.688 | 23.756 / 24.776 |
| place_reject | N/A | 0.044 / 0.055 | 15.513 / 16.313 | 15.559 / 16.359 |
| cancel | N/A | 0.009 / 0.017 | 15.527 / 16.183 | 15.537 / 16.193 |

Preview cohorts (cached polls do not claim a new visual response):

| Cache outcome | Count | Samples | Logic | Total |
|---|---:|---:|---:|---:|
| unevaluated | 1 | 270 | 0.001 / 0.002 | — |
| hit | 1 | 1350 | 0.029 / 0.068 | — |
| miss | 1 | 60 | 0.051 / 0.068 | 15.492 / 16.297 |
| hit | 2 | 270 | 0.029 / 0.056 | — |

## 10 initial buildings

| Interaction | Input → logic | Logic | Logic → backbuffer | Total replay → backbuffer |
|---|---:|---:|---:|---:|
| select | N/A | 0.031 / 0.064 | 15.908 / 17.053 | 15.939 / 17.087 |
| clear | N/A | 0.017 / 0.020 | 15.982 / 56.138 | 15.999 / 56.156 |
| switch | N/A | 0.032 / 0.069 | 15.825 / 16.705 | 15.858 / 16.761 |
| enter | N/A | 0.012 / 0.015 | 15.568 / 16.798 | 15.581 / 16.809 |
| rotate | N/A | 0.065 / 0.103 | 16.001 / 17.259 | 16.071 / 17.318 |
| place_success | N/A | 0.124 / 0.156 | 24.290 / 27.802 | 24.412 / 27.945 |
| place_reject | N/A | 0.074 / 0.100 | 16.116 / 17.488 | 16.199 / 17.553 |
| cancel | N/A | 0.009 / 0.011 | 16.265 / 16.914 | 16.275 / 16.923 |

Preview cohorts (cached polls do not claim a new visual response):

| Cache outcome | Count | Samples | Logic | Total |
|---|---:|---:|---:|---:|
| unevaluated | 10 | 270 | 0.001 / 0.011 | — |
| hit | 10 | 1350 | 0.029 / 0.145 | — |
| miss | 10 | 60 | 0.067 / 0.124 | 15.993 / 16.716 |
| hit | 11 | 270 | 0.029 / 0.083 | — |

## 100 initial buildings

| Interaction | Input → logic | Logic | Logic → backbuffer | Total replay → backbuffer |
|---|---:|---:|---:|---:|
| select | N/A | 0.049 / 0.054 | 16.026 / 17.050 | 16.073 / 17.100 |
| clear | N/A | 0.034 / 0.041 | 16.050 / 17.358 | 16.085 / 17.393 |
| switch | N/A | 0.051 / 0.204 | 16.069 / 17.409 | 16.120 / 17.462 |
| enter | N/A | 0.012 / 0.015 | 16.054 / 17.395 | 16.068 / 17.407 |
| rotate | N/A | 0.286 / 0.345 | 16.079 / 16.946 | 16.380 / 17.210 |
| place_success | N/A | 0.949 / 1.076 | 23.772 / 25.443 | 24.797 / 26.398 |
| place_reject | N/A | 0.486 / 0.565 | 15.853 / 17.345 | 16.342 / 17.898 |
| cancel | N/A | 0.009 / 0.011 | 16.447 / 17.494 | 16.457 / 17.504 |

Preview cohorts (cached polls do not claim a new visual response):

| Cache outcome | Count | Samples | Logic | Total |
|---|---:|---:|---:|---:|
| unevaluated | 100 | 270 | 0.001 / 0.002 | — |
| hit | 100 | 1350 | 0.029 / 0.171 | — |
| miss | 100 | 60 | 0.290 / 0.358 | 16.378 / 20.958 |
| hit | 101 | 270 | 0.030 / 0.050 | — |

## Placement stages

Intervals below are inclusive where applicable; do not sum overlapping validations.

| Stage | 1 building | 10 buildings | 100 buildings |
|---|---:|---:|---:|
| initial validation | 0.008 / 0.011 | 0.025 / 0.047 | 0.240 / 0.357 |
| placement evaluation | 0.008 / 0.024 | 0.020 / 0.024 | 0.217 / 0.243 |
| candidate copy | 0.002 / 0.015 | 0.004 / 0.005 | 0.013 / 0.016 |
| candidate validation | 0.007 / 0.011 | 0.018 / 0.022 | 0.215 / 0.257 |
| deferred view rebuild | 0.022 / 0.026 | 0.024 / 0.032 | 0.042 / 0.047 |
