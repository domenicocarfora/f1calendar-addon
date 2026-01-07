# Formula 1 Addon per Home Assistant

Un addon per integrare informazioni sulle gare di Formula 1 in Home Assistant.

## Descrizione

Questo addon recupera i dati delle gare di Formula 1 della stagione corrente dall'API Ergast e crea tre sensori in Home Assistant:
- **Gara precedente** (`sensor.f1_previous_race`)
- **Gara attuale** (`sensor.f1_current_race`)
- **Gara successiva** (`sensor.f1_next_race`)

Ogni sensore contiene informazioni complete sulla gara, incluse:
- Nome della gara e del circuito
- Data e ora della gara
- Date e orari delle sessioni:
  - Prove libere (FP1, FP2, FP3)
  - Qualifiche
  - Sprint (se presente)
  - Qualifiche Sprint (se presente)

## Installazione

1. Aggiungi questo repository al tuo Home Assistant
2. Vai in **Supervisor** > **Add-on Store** > **Repository**
3. Aggiungi: `https://github.com/domenicocarfora/f1calendar-addon`
4. Installa l'addon "Formula 1 Addon"
5. Configura l'addon (vedi sezione Configurazione)
6. Avvia l'addon

## Configurazione

### Opzioni disponibili

- `log_level` (string, richiesto): Livello di log. Valori possibili:
  - `fatal`
  - `error`
  - `warn`
  - `info` (default)
  - `debug`
  - `trace`

- `update_interval` (integer, richiesto): Intervallo di aggiornamento in secondi. Minimo 300 (5 minuti), massimo 86400 (24 ore). Default: 3600 (1 ora)

### Esempio di configurazione

```yaml
log_level: info
update_interval: 3600
```

## Sensori creati

Dopo l'avvio, l'addon creerà automaticamente i seguenti sensori:

### `sensor.f1_previous_race`
Contiene informazioni sulla gara precedente.

### `sensor.f1_current_race`
Contiene informazioni sulla gara attuale o imminente.

### `sensor.f1_next_race`
Contiene informazioni sulla prossima gara programmata.

Ogni sensore ha i seguenti attributi:
- `race_name`: Nome della gara
- `circuit_name`: Nome del circuito
- `country`: Paese
- `locality`: Località
- `season`: Stagione
- `round`: Numero del round
- `race_date`: Data della gara (formato originale API)
- `race_time`: Data e ora della gara in formato ISO nel fuso orario di Roma (es: `2024-05-05T15:00:00+02:00`)
- `race_time_formatted`: Data e ora formattata per Roma (es: `05/05/2024 15:00`)
- `first_practice`: Data e ora FP1 in formato ISO (fuso orario Roma)
- `first_practice_formatted`: Data e ora FP1 formattata (es: `03/05/2024 14:00`)
- `second_practice`: Data e ora FP2 in formato ISO (fuso orario Roma)
- `second_practice_formatted`: Data e ora FP2 formattata
- `third_practice`: Data e ora FP3 in formato ISO (se presente)
- `third_practice_formatted`: Data e ora FP3 formattata (se presente)
- `qualifying`: Data e ora qualifiche in formato ISO (fuso orario Roma)
- `qualifying_formatted`: Data e ora qualifiche formattata
- `sprint`: Data e ora sprint in formato ISO (se presente)
- `sprint_formatted`: Data e ora sprint formattata (se presente)
- `sprint_qualifying`: Data e ora qualifiche sprint in formato ISO (se presente)
- `sprint_qualifying_formatted`: Data e ora qualifiche sprint formattata (se presente)
- `status`: Stato della gara (completed, current, upcoming)

**Nota:** Tutti gli orari sono convertiti dal fuso orario UTC (fornito dall'API) al fuso orario di Roma (Europe/Rome), rispettando l'ora legale (CEST/CET).

## Utilizzo in Automazioni

Puoi utilizzare questi sensori nelle tue automazioni di Home Assistant:

```yaml
automation:
  - alias: "Notifica prossima gara F1"
    trigger:
      - platform: state
        entity_id: sensor.f1_next_race
    action:
      - service: notify.mobile_app
        data:
          message: "Prossima gara: {{ state_attr('sensor.f1_next_race', 'race_name') }}"
          
  - alias: "Avviso qualifiche F1"
    trigger:
      - platform: time
        at: "{{ state_attr('sensor.f1_current_race', 'qualifying') }}"
    action:
      - service: notify.all
        data:
          message: "Qualifiche F1 stanno per iniziare!"
```

## Supporto

Per problemi e richieste, apri una issue su GitHub.

## Licenza

MIT License

