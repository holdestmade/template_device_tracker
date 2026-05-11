# Template Device Tracker

A Home Assistant custom integration that adds template-driven `device_tracker` entities
— the one entity type the built-in `template` integration doesn't support natively.
Made to replace the future deprecated device_tracker.see and known_devices.yaml.
Configure either via YAML or the UI helper flow.

## Installation

Copy the `template_device_tracker` directory into `<config>/custom_components/`
and restart Home Assistant.

## UI configuration

Settings → Devices & Services → Add Integration → "Template Device Tracker".

## YAML configuration

```yaml
template_device_tracker:
  trackers:
    - name: User's phone (derived)
      unique_id: users_phone_template
      state: >-
        {% if is_state('person.user', 'home') %}home
        {% elif is_state('person.user', 'work') %}work
        {% else %}not_home{% endif %}
      latitude: "{{ state_attr('person.user', 'latitude') }}"
      longitude: "{{ state_attr('person.user', 'longitude') }}"
      gps_accuracy: "{{ state_attr('person.user', 'gps_accuracy') | int(0) }}"
      altitude: "{{ state_attr('person.user', 'altitude') | float(0) }}"
      speed: "{{ state_attr('person.user', 'speed') | float(0) }}"
      course: "{{ state_attr('person.user', 'course') | float(0) }}"
      satellites: "{{ state_attr('person.user', 'satellites') | int(0) }}"
      battery_level: "{{ states('sensor.user_phone_battery') | int(0) }}"
      icon: mdi:cellphone
      availability: "{{ has_value('person.user') }}"
      attributes:
        last_seen: "{{ states.person.user.last_changed }}"
```


## Fields

| Field | Required | Notes |
|-------|----------|-------|
| `name` | yes | Plain string; renders as friendly_name. |
| `state` | no | Returns `home`, `not_home`, or a zone name. Booleans and `true`/`false` are accepted and mapped. |
| `latitude` / `longitude` | no | Floats. If both are set, `source_type` defaults to `gps`. |
| `gps_accuracy` | no | Horizontal accuracy, metres. Defaults to 0. Drives `TrackerEntity.location_accuracy`. |
| `altitude` | no | Metres above sea level. Exposed as `altitude` state attribute. |
| `speed` | no | Float; unit determined by your source. Exposed as `speed` state attribute. |
| `course` | no | Degrees (0–360). Exposed as `course` state attribute. |
| `satellites` | no | Integer; satellites in view. Exposed as `satellites` state attribute. |
| `battery_level` | no | Coerced to int (0–100). |
| `picture` | no | URL string. |
| `icon` | no | mdi icon. |
| `availability` | no | Truthy/falsy; entity goes `unavailable` on false. |
| `source_type` | no | One of `gps`, `router`, `bluetooth`, `bluetooth_le`. |
| `attributes` | no | Mapping of attribute name → template; merged into state attributes alongside altitude/speed/course/satellites. |

## Notes

- Templates are tracked with `async_track_template_result`, so updates are
  push-driven — no polling.
- Transient template errors do not clear last-known values (except for
  `availability`, where an error sets the entity to unavailable).
- `altitude`, `speed`, `course` and `satellites` are not native
  `TrackerEntity` properties in Home Assistant, so they are exposed as
  state attributes — matching the convention used by `mobile_app`,
  OwnTracks and GPSLogger.
- Tested against Home Assistant 2024.x and 2025.x APIs.
