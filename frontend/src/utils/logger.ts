type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LoggerConfig {
  level: LogLevel
  prefix?: string
  enableConsole: boolean
}

class Logger {
  private isDev: boolean
  private prefix: string
  private enableConsole: boolean
  private levelPriority: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3
  }
  private currentLevel: LogLevel

  constructor(config?: Partial<LoggerConfig>) {
    this.isDev = import.meta.env.DEV
    this.prefix = config?.prefix || '[FuturisticBlog]'
    this.enableConsole = config?.enableConsole ?? true
    this.currentLevel = config?.level || (this.isDev ? 'debug' : 'error')
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.enableConsole) return false
    return this.levelPriority[level] >= this.levelPriority[this.currentLevel]
  }

  private formatMessage(level: LogLevel, ...args: any[]): any[] {
    const timestamp = new Date().toISOString()
    const levelTag = `[${level.toUpperCase()}]`
    return [`${this.prefix}${levelTag}`, `[${timestamp}]`, ...args]
  }

  debug(...args: any[]): void {
    if (this.shouldLog('debug') && this.isDev) {
      console.debug(...this.formatMessage('debug', ...args))
    }
  }

  info(...args: any[]): void {
    if (this.shouldLog('info')) {
      console.info(...this.formatMessage('info', ...args))
    }
  }

  warn(...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn(...this.formatMessage('warn', ...args))
    }
  }

  error(...args: any[]): void {
    if (this.shouldLog('error')) {
      console.error(...this.formatMessage('error', ...args))
    }
  }

  group(label: string): void {
    if (this.isDev && this.enableConsole) {
      console.group(label)
    }
  }

  groupEnd(): void {
    if (this.isDev && this.enableConsole) {
      console.groupEnd()
    }
  }

  time(label: string): void {
    if (this.isDev && this.enableConsole) {
      console.time(label)
    }
  }

  timeEnd(label: string): void {
    if (this.isDev && this.enableConsole) {
      console.timeEnd(label)
    }
  }

  table(data: any): void {
    if (this.isDev && this.enableConsole) {
      console.table(data)
    }
  }

  setLevel(level: LogLevel): void {
    this.currentLevel = level
  }

  createChild(childPrefix: string): Logger {
    return new Logger({
      prefix: `${this.prefix}:${childPrefix}`,
      level: this.currentLevel,
      enableConsole: this.enableConsole
    })
  }
}

export const logger = new Logger()

export const createLogger = (prefix: string): Logger => {
  return logger.createChild(prefix)
}

export default logger
