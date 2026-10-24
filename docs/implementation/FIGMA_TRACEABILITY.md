# Figma frame → runtime trace

83 active design frames map to one application state model. Repeated playback/filter/sidebar variants are states, not separate websites. All route mappings below are implemented; representative visual tests are identified separately from unrendered combinations.

| Frame | Name | Runtime state | Component | API | Test coverage |
|---|---|---|---|---|---|
| 74:2 | FLUO_V2/overview | #/ | Views.tsx / Overview | /sessions/{id} | HGB readings, geometry, Full/Compact |
| 74:107 | FLUO_V2/lab | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 74:198 | FLUO_V2/events | #/events + category state | Views.tsx / EventCenter | /sessions/{id}/events | filter, sort, event navigation |
| 74:302 | FLUO_V2/details | #/events/{id} | Views.tsx / EventDetails | /sessions/{id}/events/{id} | four event checklists; Full/Compact |
| 96:2 | FLUO_FLOW/lab-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 96:130 | FLUO_FLOW/lab-paused | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 96:253 | FLUO_FLOW/lab-normal | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 96:383 | FLUO_FLOW/events-filtered | #/events + category state | Views.tsx / EventCenter | /sessions/{id}/events | filter, sort, event navigation |
| 100:2 | FLUO_FLOW/lab-pipe-loss | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 100:125 | FLUO_FLOW/lab-trap | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 100:248 | FLUO_FLOW/lab-meter | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 100:371 | FLUO_FLOW/lab-delay | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 100:494 | FLUO_FLOW/lab-outage | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 100:620 | FLUO_FLOW/lab-speed-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 100:748 | FLUO_FLOW/lab-normal-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 101:2 | FLUO_FLOW/event-mode | #/events/{id} | Views.tsx / EventDetails | /sessions/{id}/events/{id} | four event checklists; Full/Compact |
| 101:107 | FLUO_FLOW/event-meter | #/events/{id} | Views.tsx / EventDetails | /sessions/{id}/events/{id} | four event checklists; Full/Compact |
| 101:212 | FLUO_FLOW/event-restored | #/events/{id} | Views.tsx / EventDetails | /sessions/{id}/events/{id} | four event checklists; Full/Compact |
| 102:2 | FLUO_FLOW/lab-pipe-loss-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 102:125 | FLUO_FLOW/lab-trap-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 102:248 | FLUO_FLOW/lab-meter-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 102:371 | FLUO_FLOW/lab-delay-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 102:494 | FLUO_FLOW/lab-outage-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 102:620 | FLUO_FLOW/lab-normal-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 103:2 | FLUO_FLOW/lab-pipe-loss-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 103:125 | FLUO_FLOW/lab-trap-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 103:248 | FLUO_FLOW/lab-meter-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 103:371 | FLUO_FLOW/lab-delay-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 103:494 | FLUO_FLOW/lab-outage-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 124:2 | FLUO_FLOW/events-quality | #/events + category state | Views.tsx / EventCenter | /sessions/{id}/events | filter, sort, event navigation |
| 124:131 | FLUO_FLOW/filter-all | #/events + filter overlay | App.tsx / filter Dialog | /sessions/{id}/events | filter categories Full/Compact |
| 124:289 | FLUO_FLOW/filter-return | #/events + filter overlay | App.tsx / filter Dialog | /sessions/{id}/events | filter categories Full/Compact |
| 124:447 | FLUO_FLOW/filter-quality | #/events + filter overlay | App.tsx / filter Dialog | /sessions/{id}/events | filter categories Full/Compact |
| 128:5 | FLUO_COMPACT/FLUO_V2/overview | #/ | Views.tsx / Overview | /sessions/{id} | HGB readings, geometry, Full/Compact |
| 128:144 | FLUO_COMPACT/FLUO_V2/lab | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:286 | FLUO_COMPACT/FLUO_V2/events | #/events + category state | Views.tsx / EventCenter | /sessions/{id}/events | filter, sort, event navigation |
| 128:422 | FLUO_COMPACT/FLUO_V2/details | #/events/{id} | Views.tsx / EventDetails | /sessions/{id}/events/{id} | four event checklists; Full/Compact |
| 128:1171 | FLUO_COMPACT/FLUO_FLOW/lab-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:1318 | FLUO_COMPACT/FLUO_FLOW/lab-paused | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:1460 | FLUO_COMPACT/FLUO_FLOW/lab-normal | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:1601 | FLUO_COMPACT/FLUO_FLOW/events-filtered | #/events + category state | Views.tsx / EventCenter | /sessions/{id}/events | filter, sort, event navigation |
| 128:1734 | FLUO_COMPACT/FLUO_FLOW/lab-pipe-loss | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:1875 | FLUO_COMPACT/FLUO_FLOW/lab-trap | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:2016 | FLUO_COMPACT/FLUO_FLOW/lab-meter | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:2157 | FLUO_COMPACT/FLUO_FLOW/lab-delay | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:2298 | FLUO_COMPACT/FLUO_FLOW/lab-outage | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:2444 | FLUO_COMPACT/FLUO_FLOW/lab-speed-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:2591 | FLUO_COMPACT/FLUO_FLOW/lab-normal-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:2858 | FLUO_COMPACT/FLUO_FLOW/event-mode | #/events/{id} | Views.tsx / EventDetails | /sessions/{id}/events/{id} | four event checklists; Full/Compact |
| 128:2998 | FLUO_COMPACT/FLUO_FLOW/event-meter | #/events/{id} | Views.tsx / EventDetails | /sessions/{id}/events/{id} | four event checklists; Full/Compact |
| 128:3123 | FLUO_COMPACT/FLUO_FLOW/event-restored | #/events/{id} | Views.tsx / EventDetails | /sessions/{id}/events/{id} | four event checklists; Full/Compact |
| 128:3246 | FLUO_COMPACT/FLUO_FLOW/lab-pipe-loss-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:3387 | FLUO_COMPACT/FLUO_FLOW/lab-trap-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:3528 | FLUO_COMPACT/FLUO_FLOW/lab-meter-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:3669 | FLUO_COMPACT/FLUO_FLOW/lab-delay-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:3810 | FLUO_COMPACT/FLUO_FLOW/lab-outage-playing | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:3956 | FLUO_COMPACT/FLUO_FLOW/lab-normal-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:4097 | FLUO_COMPACT/FLUO_FLOW/lab-pipe-loss-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:4238 | FLUO_COMPACT/FLUO_FLOW/lab-trap-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:4379 | FLUO_COMPACT/FLUO_FLOW/lab-meter-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:4520 | FLUO_COMPACT/FLUO_FLOW/lab-delay-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:4661 | FLUO_COMPACT/FLUO_FLOW/lab-outage-2x | #/scenarios + recorded scenario/playback state | Views.tsx / ScenarioReview | /sessions/{id}/replay | scenario reset, pause, speed, rewind, seek |
| 128:4807 | FLUO_COMPACT/FLUO_FLOW/events-quality | #/events + category state | Views.tsx / EventCenter | /sessions/{id}/events | filter, sort, event navigation |
| 128:4943 | FLUO_COMPACT/FLUO_FLOW/filter-all | #/events + filter overlay | App.tsx / filter Dialog | /sessions/{id}/events | filter categories Full/Compact |
| 128:5110 | FLUO_COMPACT/FLUO_FLOW/filter-return | #/events + filter overlay | App.tsx / filter Dialog | /sessions/{id}/events | filter categories Full/Compact |
| 128:5277 | FLUO_COMPACT/FLUO_FLOW/filter-quality | #/events + filter overlay | App.tsx / filter Dialog | /sessions/{id}/events | filter categories Full/Compact |
| 130:2 | FLUO_PRINT/A4 Inspection EV-018 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 170:2 | FLUO_OVERLAY/notifications | current route + contextual overlay | App.tsx / contextual Dialog | /sessions/{id} and /preferences | contextual overlays and focus |
| 170:31 | FLUO_OVERLAY/help | current route + contextual overlay | App.tsx / contextual Dialog | /sessions/{id} and /preferences | contextual overlays and focus |
| 170:47 | FLUO_OVERLAY/preferences | current route + contextual overlay | App.tsx / contextual Dialog | /sessions/{id} and /preferences | contextual overlays and focus |
| 170:70 | FLUO_OVERLAY/preferences-off | current route + contextual overlay | App.tsx / contextual Dialog | /sessions/{id} and /preferences | contextual overlays and focus |
| 170:93 | FLUO_OVERLAY/profile | current route + contextual overlay | App.tsx / contextual Dialog | /sessions/{id} and /preferences | contextual overlays and focus |
| 170:106 | FLUO_OVERLAY/inspection-summary | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 173:2 | FLUO_OVERLAY/inspection-EV-017 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 173:14 | FLUO_PRINT/A4 Inspection EV-017 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 173:65 | FLUO_OVERLAY/inspection-EV-016 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 173:77 | FLUO_PRINT/A4 Inspection EV-016 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 173:128 | FLUO_OVERLAY/inspection-EV-015 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 173:140 | FLUO_PRINT/A4 Inspection EV-015 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 186:34 | FLUO_OVERLAY/print-preview-EV-018 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 186:106 | FLUO_OVERLAY/print-preview-EV-017 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 186:178 | FLUO_OVERLAY/print-preview-EV-016 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |
| 186:250 | FLUO_OVERLAY/print-preview-EV-015 | #/events/{id} + summary/preview | App.tsx / summary + preview; backend/reporting.py | /events/{id}/report.pdf and /print | four event PDFs and print calls |