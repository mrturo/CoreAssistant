# CoreAssistant

A productivity assistant that integrates Google Tasks, Google Calendar and Todoist to manage tasks and events in a unified way.

## Features

- ✅ **Google Tasks**: Get, organize and auto-complete tasks
- 📅 **Google Calendar**: Display upcoming events
- 🎯 **Todoist**: Complete integration with projects, labels and filters
- 🔄 **Auto-completion**: Automatically complete parent tasks when all subtasks are complete
- 📊 **Unified view**: Organize all items by time periods
- 🎨 **Clear presentation**: Structured text format with relevant details

## Configuration

### 1. Configure Google APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Tasks and Google Calendar APIs
4. Create OAuth 2.0 credentials for desktop application
5. Download the credentials JSON file to `config/gcp/credentials.json`

### 2. Configure Todoist (Optional)

1. Go to [Todoist Settings → Integrations](https://todoist.com/prefs/integrations)
2. Copy your API token
3. Create a `.env` file based on `.env.example`
4. Add your token: `TODOIST_API_TOKEN=your_token_here`

### 3. Installation

```bash
# Install dependencies
bash envtool.sh install prod

# Or for development
bash envtool.sh install dev
```

## Usage

### Basic command (Google only)
```bash
bash runtasks.sh planned_item
```

### All sources (Google + Todoist)
```bash
bash runtasks.sh planned_item_all
```

### Todoist examples
```bash
bash runtasks.sh todoist_example
```

### Environment variables

You can control the behavior with environment variables:

```bash
# Force specific mode
export COREASSISTANT_MODE=google    # Google only
export COREASSISTANT_MODE=todoist   # Todoist only  
export COREASSISTANT_MODE=all       # All sources
export COREASSISTANT_MODE=auto      # Auto-detect (default)

# Run
bash runtasks.sh all
```

## Todoist Filters

The integration supports native Todoist filters:

- `today` - Today's tasks
- `overdue` - Overdue tasks
- `p1`, `p2`, `p3`, `p4` - By priority
- `no date` - Tasks without date
- `@label` - By label
- `#Project` - By project
- `assigned to: me` - Assigned to you

## Development

```bash
# Check code
bash envtool.sh code-check

# Run tests
bash envtool.sh test

# Clear cache
bash envtool.sh clean-cache
```
