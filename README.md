---
title: Claim Checker
emoji: 🦀
colorFrom: pink
colorTo: indigo
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
short_description: Helps you decipher wheter a claim is true or false.
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

### Architecture

```plantuml
@startuml app architecture
skinparam componentStyle rectangle
' left to right direction

' Define main components
label Claim

label "unsloth zoo" as unsloth

[Query Articles] as query
[Parse Responses] as parser
[Stance Shaping] as shaping
[UI] as ui

package modal {
    [Stance Inference] as inference
    [Load Model] as load_model
}

' Connections between components
Claim --> query
query -> inference : articles
load_model --> inference : model
unsloth --> load_model
inference -> parser : responses
parser -> shaping: status
ui <-- shaping

@enduml
* ```
