# Formula 1 Calendar Integration per Home Assistant

Un'integrazione per integrare informazioni sulle gare di Formula 1 in Home Assistant.

## Descrizione

Questa integrazione recupera i dati delle gare di Formula 1 della stagione corrente dall'API Ergast e crea tre sensori in Home Assistant:
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

### Metodo 1: HACS (Consigliato)

1. Assicurati che [HACS](https://hacs.xyz/) sia installato
2. Vai su **HACS** > **Integrations**
3. Clicca sui tre puntini in alto a destra e seleziona **Custom repositories**
4. Aggiungi il repository:
   - Repository: `https://github.com/domenicocarfora/f1calendar-addon`
   - Category: **Integration**
5. Cerca "Formula 1 Calendar" e installalo
6. Riavvia Home Assistant

### Metodo 2: Manuale

1. Scarica o clona questo repository
2. Copia la cartella `custom_components/f1calendar` nella directory `custom_components` della tua installazione Home Assistant
   - Se non esiste, crea la cartella `custom_components` nella root della configurazione HA
3. Riavvia Home Assistant
4. Vai su **Impostazioni** > **Dispositivi e servizi** > **Aggiungi integrazione**
5. Cerca "Formula 1 Calendar" e configurala

## Configurazione

Dopo l'installazione:

1. Vai su **Impostazioni** > **Dispositivi e servizi**
2. Clicca su **Aggiungi integrazione**
3. Cerca "Formula 1 Calendar"
4. Durante la configurazione puoi impostare:
   - **Intervallo di aggiornamento**: da 300 secondi (5 minuti) a 86400 secondi (24 ore). Default: 3600 secondi (1 ora)

### Configurazione via YAML (Opzionale)

Puoi anche aggiungere l'integrazione tramite `configuration.yaml`:

```yaml
f1calendar:
  scan_interval: 3600  # Opzionale, in secondi
```

## Sensori creati

Dopo la configurazione, l'integrazione creerà automaticamente i seguenti sensori:

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

## Requisiti

- Home Assistant 2023.1.0 o superiore
- Connessione internet (per accedere all'API Ergast)

## Supporto

Per problemi e richieste, apri una issue su [GitHub](https://github.com/domenicocarfora/f1calendar-addon/issues).

## Licenza

MIT License
