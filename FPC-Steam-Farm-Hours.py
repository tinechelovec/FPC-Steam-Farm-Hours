from __future__ import annotations
import copy, hashlib, html, json, logging, os, platform, re, secrets, shutil, subprocess, tarfile, tempfile, threading, time, uuid, zipfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional
import requests
try:
    from tg_bot import CBT as _CBT
except Exception:
    _CBT = None
try:
    from telebot import types as tg_types
except Exception:
    tg_types = None
NAME = 'Steam Farm Hours'
VERSION = '1.1.0'
DESCRIPTION = 'Автоматическая продажа фарма часов Steam'
CREDITS = '@dmitry_mak09, @tinechelovec'
UUID = 'ad850697-49bd-481d-8660-2c06f16b5813'
BASE_URL = 'https://api.dim4n4ik.shop'
SHOP_BOT_URL = 'https://t.me/dim4n4ikshop_bot?start=ref7202094913'
CREATOR_URL = 'https://t.me/tinechelovec'
SERVICE_AUTHOR_URL = 'https://t.me/dmitry_mak09'
GROUP_URL = 'https://t.me/dev_thc_chat'
CHANNEL_URL = 'https://t.me/by_thc'
SHOP_CHAT_URL = 'https://t.me/berloga_dim4n4ik'
SHOP_SITE_URL = 'https://dim4n4ik.shop'
INSTRUCTION_URL = 'https://teletype.in/@tinechelovec/Steam-Farm-Hours'
ALT_INSTRUCTION_URL = 'https://github.com/tinechelovec/FPC-Steam-Farm-Hours/blob/main/instructions.md'
GITHUB_URL = 'https://github.com/tinechelovec/FPC-Steam-Farm-Hours'
GITHUB_REPO = 'tinechelovec/FPC-Steam-Farm-Hours'
AUTO_LOT_CATEGORIES = (1009, 1351)
PERIOD_DISCOUNTS = {1: 0, 3: 16, 6: 26, 12: 41}
SLOT_RESERVATION_TTL_SEC = 15 * 60
STORAGE_DIR = os.path.join('storage', 'plugins', 'dim4n4ik_steam_farm')
LOG_DIR = os.path.join(STORAGE_DIR, 'logs')
CONFIG_FILE = os.path.join(STORAGE_DIR, 'settings.json')
BINDINGS_FILE = os.path.join(STORAGE_DIR, 'lots.json')
SERVICES_FILE = os.path.join(STORAGE_DIR, 'services.json')
AUTO_DISABLED_FILE = os.path.join(STORAGE_DIR, 'auto_disabled.json')
NOTIFY_STATE_FILE = os.path.join(STORAGE_DIR, 'notify_state.json')
LOG_FILE = os.path.join(LOG_DIR, 'plugin.log')
LOCAL_DIR = os.path.join(STORAGE_DIR, 'local')
LOCAL_HELPER_FILE = os.path.join(LOCAL_DIR, 'steamfarm_helper.js')
LOCAL_PACKAGE_FILE = os.path.join(LOCAL_DIR, 'package.json')
LOCAL_META_FILE = os.path.join(LOCAL_DIR, 'meta.json')
LOCAL_DAEMON_LOG = os.path.join(LOG_DIR, 'local-daemon.log')
LOCAL_RUNTIME_DIR = os.path.join(LOCAL_DIR, 'runtime')
LOCAL_NODE_DIST = 'https://nodejs.org/dist'
LOCAL_DEFAULT_PORT = 28745
LOCAL_STEAM_USER_VERSION = '^5.2.0'
LOCAL_SOURCE_URL = 'https://github.com/ZixeSea/SteamIdler'
_CBT_PLUGIN_SETTINGS = getattr(_CBT, 'PLUGIN_SETTINGS', None) if _CBT else None
CBT_SETTINGS = f'{_CBT_PLUGIN_SETTINGS}:{UUID}:0' if _CBT_PLUGIN_SETTINGS is not None else ''
SETTINGS_PAGE = False
CB_PLUGINS_LIST_OPEN = f"{getattr(_CBT, 'PLUGINS_LIST', '44')}:0" if _CBT else '44:0'
logger = logging.getLogger('FPC.dim4n4ik_steam_farm')
LP = '[steamfarm]'
DEFAULT_MESSAGES = {'order_paid': '👋 Привет! Спасибо за заказ #{order_id}.\n\nОплата получена. Чтобы начать фарм, отправьте, пожалуйста, логин Steam одним сообщением. Затем я попрошу пароль и, если понадобится, код Steam Guard.\n\nДанные используются только для подключения аккаунта к услуге.', 'queued': '👋 Привет! Спасибо за заказ #{order_id}.\n\nОплата получена. Сейчас все места заняты, поэтому заказ поставлен в очередь. Ваша позиция: {position}.\nЯ сам напишу, когда освободится место — ничего дополнительно делать пока не нужно.', 'slot_available': '✅ По заказу #{order_id} освободилось место. Можно начинать.\n\nОтправьте, пожалуйста, логин Steam одним сообщением.', 'ask_password': 'Спасибо! Теперь отправьте пароль Steam одним сообщением. Он нужен только для входа через сервис и не сохраняется', 'ask_guard': '🛡 Steam запросил код Steam Guard. Отправьте одноразовый код следующим сообщением. Код используется только для текущего входа.', 'ask_games': '🎮 Аккаунт подключён. Теперь отправьте AppID игр через пробел, например: 730 570.\nДля этого заказа можно указать максимум {max_games} игр.', 'farm_started': '🚀 Всё готово! Фарм часов запущен.\n\nИгры: {games}\nОплаченное время: {hours} ч.\nПлановое окончание: {end_time}.\n\nМожно заниматься своими делами — по завершении я напишу сюда.', 'farm_completed': '✅ Готово! Оплаченное время по заказу #{order_id} отработано, фарм остановлен.\n\nСпасибо за заказ! Если всё в порядке, можете подтвердить выполнение заказа на FunPay.', 'blocked': '👋 Заказ #{order_id} получен, но автоматический запуск сейчас временно недоступен. Продавец уже уведомлён.\nПричина: {reason}\n\nКак только ситуацию можно будет продолжить автоматически, плагин это сделает.', 'auto_refund': '↩️ По заказу #{order_id} выполнен автоматический возврат, потому что услугу сейчас нельзя безопасно выполнить.\nПричина: {reason}', 'stopped_manual': '⏹ Фарм по заказу #{order_id} досрочно остановлен продавцом.', 'refunded': '↩️ Фарм по заказу #{order_id} остановлен после возврата средств на FunPay.', 'login_invalid': '⚠️ Пожалуйста, отправьте только логин Steam одним сообщением, без дополнительного текста.', 'login_failed': '⚠️ Не удалось войти в Steam: {reason}\nПроверьте пароль и отправьте его ещё раз.', 'account_connect_failed': '⚠️ Steam-аккаунт подключился не полностью. Продавец уже уведомлён. Попробуйте ещё раз немного позже.', 'guard_bad_code': '⚠️ Код Steam Guard не подошёл. Отправьте новый одноразовый код.', 'guard_expired': '⌛ Сессия входа истекла. Отправьте пароль Steam ещё раз — подключение начнётся заново.', 'guard_failed': '⚠️ Steam Guard не принят: {reason}\nМожно попробовать отправить новый код.', 'games_invalid': '⚠️ Не удалось определить AppID. Отправьте числа через пробел, например 730 570. Максимум: {max_games}.', 'farm_start_failed': '⚠️ Не получилось запустить фарм: {reason}\nДанные заказа сохранены. Попробуйте ещё раз немного позже.'}
MESSAGE_LABELS = {'order_paid': '👋 После оплаты', 'queued': '🕒 Постановка в очередь', 'slot_available': '✅ Место освободилось', 'ask_password': '🔐 Запрос пароля', 'ask_guard': '🛡 Запрос Steam Guard', 'ask_games': '🎮 Запрос игр', 'farm_started': '🚀 Фарм запущен', 'farm_completed': '✅ Фарм завершён', 'blocked': '⚠️ Запуск недоступен', 'auto_refund': '↩️ Автовозврат', 'stopped_manual': '⏹ Остановлен продавцом', 'refunded': '↩️ Возврат FunPay', 'login_invalid': '⚠️ Некорректный логин', 'login_failed': '🔐 Ошибка входа', 'account_connect_failed': '⚠️ Ошибка подключения', 'guard_bad_code': '🛡 Неверный Guard', 'guard_expired': '⌛ Guard истёк', 'guard_failed': '🛡 Ошибка Guard', 'games_invalid': '🎮 Некорректные игры', 'farm_start_failed': '⚠️ Ошибка запуска'}
MESSAGE_FIELDS = {'order_id', 'buyer', 'hours', 'reason', 'position', 'games', 'end_time', 'max_games', 'lot_id', 'quantity'}
DEFAULT_CONFIG: Dict[str, Any] = {'api_key': '', 'farm_backend': 'api', 'local_max_accounts': 3, 'local_max_games': 32, 'local_port': LOCAL_DEFAULT_PORT, 'plugin_enabled': True, 'notifications_enabled': True, 'auto_refund_enabled': False, 'auto_deactivate_on_slots': True, 'queue_enabled': False, 'safety_buffer_hours': 1.0, 'capacity_check_sec': 60, 'notify_near_expiry': True, 'notify_new_order': True, 'notify_started': True, 'notify_completed': True, 'notify_errors': True, 'notify_subscription': True, 'notify_capacity': True, 'notify_reconnect': True, 'stats_reset_at': 0.0, 'messages': copy.deepcopy(DEFAULT_MESSAGES)}
ERROR_HUMAN = {'unauthorized': 'API-ключ не принят.', 'invalid_key': 'API-ключ неверен или отозван.', 'forbidden': 'У API-ключа нет нужных прав.', 'insufficient_balance': 'Недостаточно средств на балансе API.', 'not_found': 'Объект не найден.', 'farm_unavailable': 'Фарм сейчас недоступен на стороне сервиса.', 'no_subscription': 'Нет активной подписки на фарм.', 'limit_reached': 'Достигнут лимит Steam-аккаунтов тарифа.', 'trial_used': 'Пробный тариф уже использован.', 'bad_period': 'Некорректный срок подписки.', 'no_plan': 'Такой тариф не найден.', 'too_many_games': 'Указано слишком много игр.', 'over_plan': 'Превышен лимит тарифа.', 'too_many_logins': 'Слишком много попыток входа в Steam. Попробуйте позже.', 'steam_login_failed': 'Steam не принял вход или временно недоступен.', 'bad_code': 'Код Steam Guard не подошёл. Можно попробовать другой код.', 'login_expired': 'Сессия входа устарела. Начните подключение заново.', 'rate_limited': 'Слишком много запросов. Попробуйте немного позже.', 'quota_exceeded': 'Превышена квота API.', 'invalid_request': 'API отклонил параметры запроса.'}
FINAL_SERVICE_STEPS = {'completed', 'stopped_manual', 'disconnected', 'refunded'}
WAITING_SERVICE_STEPS = {'await_login', 'await_password', 'await_guard', 'await_games'}
cardinal = None
bot = None
admin_chat_id: Optional[int] = None
_config: Dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
_client: Optional['FarmClient'] = None
_local_client: Optional['LocalFarmClient'] = None
_local_process = None
_local_process_lock = threading.RLock()
_waiting: Dict[int, Dict[str, Any]] = {}
_purchase_confirm: Dict[int, Dict[str, Any]] = {}
_bindings: Dict[str, Dict[str, Any]] = {}
_services: Dict[str, Dict[str, Any]] = {}
_auto_disabled: Dict[str, float] = {}
_notify_state: Dict[str, Any] = {}
_farm_discovery_cache: Dict[str, Dict[str, Any]] = {}
_config_lock = threading.RLock()
_state_lock = threading.RLock()
_snapshot_lock = threading.RLock()
_update_lock = threading.Lock()
_stop_event = threading.Event()
_snapshot_cache = {'ts': 0.0, 'sub': None, 'accounts': None}
def _ensure_dirs():
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOCAL_DIR).mkdir(parents=True, exist_ok=True)
def _atomic_json(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + '.tmp')
    with temp.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, target)
def _json_dict(path):
    try:
        with Path(path).open('r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
def _load_config():
    result = copy.deepcopy(DEFAULT_CONFIG)
    raw = _json_dict(CONFIG_FILE)
    for key in DEFAULT_CONFIG:
        if key in raw:
            if key == 'messages' and isinstance(raw[key], dict):
                merged = copy.deepcopy(DEFAULT_MESSAGES)
                for mk, v in raw[key].items():
                    if mk in merged and isinstance(v, str) and v.strip():
                        merged[mk] = v[:1800]
                result[key] = merged
            else:
                result[key] = raw[key]
    result['api_key'] = str(result.get('api_key') or '').strip()
    result['farm_backend'] = str(result.get('farm_backend') or 'api').strip().lower()
    if result['farm_backend'] not in ('api', 'local'):
        result['farm_backend'] = 'api'
    try:
        result['local_max_accounts'] = max(1, min(100, int(result.get('local_max_accounts', 3) or 3)))
    except Exception:
        result['local_max_accounts'] = 3
    try:
        result['local_max_games'] = max(1, min(32, int(result.get('local_max_games', 32) or 32)))
    except Exception:
        result['local_max_games'] = 32
    try:
        result['local_port'] = max(1024, min(65535, int(result.get('local_port', LOCAL_DEFAULT_PORT) or LOCAL_DEFAULT_PORT)))
    except Exception:
        result['local_port'] = LOCAL_DEFAULT_PORT
    for key in ('plugin_enabled', 'notifications_enabled', 'auto_refund_enabled', 'auto_deactivate_on_slots', 'queue_enabled', 'notify_near_expiry', 'notify_new_order', 'notify_started', 'notify_completed', 'notify_errors', 'notify_subscription', 'notify_capacity', 'notify_reconnect'):
        result[key] = bool(result.get(key, DEFAULT_CONFIG[key]))
    try:
        result['safety_buffer_hours'] = max(0.0, min(24.0, float(result.get('safety_buffer_hours', 1))))
    except Exception:
        result['safety_buffer_hours'] = 1.0
    try:
        result['capacity_check_sec'] = max(30, min(3600, int(result.get('capacity_check_sec', 60))))
    except Exception:
        result['capacity_check_sec'] = 60
    try:
        result['stats_reset_at'] = max(0.0, float(result.get('stats_reset_at', 0)))
    except Exception:
        result['stats_reset_at'] = 0.0
    return result
def _save_config():
    with _config_lock:
        _atomic_json(CONFIG_FILE, {k: copy.deepcopy(_config.get(k, v)) for k, v in DEFAULT_CONFIG.items()})
def cfg_get(key):
    with _config_lock:
        return _config.get(key, DEFAULT_CONFIG.get(key))
def cfg_set(key, value):
    global _client, _local_client
    with _config_lock:
        _config[key] = value
        _save_config()
    if key == 'api_key':
        _client = None
        _invalidate_snapshot()
    elif key in {'farm_backend', 'local_max_accounts', 'local_max_games', 'local_port'}:
        _local_client = None
        _invalidate_snapshot()
def _configure_logging():
    try:
        _ensure_dirs()
        target = os.path.normcase(str(Path(LOG_FILE).resolve()))
        for h in logger.handlers:
            if isinstance(h, logging.FileHandler) and os.path.normcase(str(Path(getattr(h, 'baseFilename', '')).resolve())) == target:
                return
        h = logging.FileHandler(LOG_FILE, encoding='utf-8')
        h.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.addHandler(h)
    except Exception:
        pass
def _close_logging():
    for h in list(logger.handlers):
        if isinstance(h, logging.FileHandler):
            try:
                h.flush()
                logger.removeHandler(h)
                h.close()
            except Exception:
                pass
def _log_event(event, level=logging.INFO, **fields):
    parts = [f'event={str(event)[:80]}']
    for k, v in fields.items():
        text = '***' if any((w in str(k).lower() for w in ('key', 'password', 'guard', 'token', 'code'))) else str(v).replace('\r', ' ').replace('\n', ' ')[:260]
        parts.append(f'{str(k)[:60]}={text}')
    logger.log(level, f'{LP} ' + ' '.join(parts))
class FarmApiError(Exception):
    def __init__(self, http, code, message, extra=None):
        super().__init__(f'{code}: {message}')
        self.http = int(http)
        self.code = str(code)
        self.message = str(message)
        self.extra = extra or {}
class FarmNetworkError(Exception):
    pass
class LocalFarmError(Exception):
    def __init__(self, code, message, extra=None):
        super().__init__(f'{code}: {message}')
        self.code = str(code or 'local_error')
        self.message = str(message or self.code)
        self.extra = extra or {}
def _backend_mode():
    value = str(cfg_get('farm_backend') or 'api').strip().lower()
    return value if value in ('api', 'local') else 'api'
def _backend_label(value=None):
    return '🖥 Local (бесплатно)' if str(value or _backend_mode()).lower() == 'local' else '☁️ API dim4n4ik'
def _active_service_count():
    with _state_lock:
        return sum(1 for v in _services.values() if isinstance(v, dict) and str(v.get('step') or '') not in FINAL_SERVICE_STEPS)
def _can_switch_backend(target):
    target = str(target or '').strip().lower()
    if target not in ('api', 'local'):
        return (False, 'Неизвестный движок.')
    if target == _backend_mode():
        return (True, '')
    active = _active_service_count()
    if active:
        return (False, f'Сейчас есть активные заказы: {active}. Сначала завершите или остановите их.')
    return (True, '')
def _switch_backend(target):
    ok, reason = _can_switch_backend(target)
    if not ok:
        return (False, reason)
    target = str(target).strip().lower()
    if target != _backend_mode():
        cfg_set('farm_backend', target)
        _log_event('backend_switched', backend=target)
    return (True, '')
def _local_subscription_snapshot():
    return {
        'active': True,
        'backend': 'local',
        'plan': 'local',
        'plan_name': 'Local / бесплатно',
        'accounts': max(1, int(cfg_get('local_max_accounts') or 3)),
        'games': max(1, min(32, int(cfg_get('local_max_games') or 32))),
        'expires_at': None,
    }
LOCAL_HELPER_SOURCE = r"""'use strict';
const http = require('http');
const SteamUser = require('steam-user');

const PORT = Number.parseInt(process.env.STEAMFARM_PORT || '28745', 10);
const TOKEN = String(process.env.STEAMFARM_TOKEN || '');
const HOST = '127.0.0.1';
const sessions = new Map();
let nextId = 1;

function safeError(err) {
  if (!err) return 'Steam error';
  return String(err.message || err.eresult || err).slice(0, 300);
}

function publicSession(s) {
  return {
    id: s.id,
    login: s.login,
    state: s.state,
    running: !!s.running,
    games: Array.isArray(s.games) ? s.games : [],
    connected: !!s.connected,
    needs_reconnect: ['error', 'disconnected'].includes(s.state),
    error: s.lastError || ''
  };
}

function signal(s, payload) {
  const waiters = s.waiters.splice(0, s.waiters.length);
  for (const waiter of waiters) waiter(payload);
}

function waitForSignal(s, timeoutMs = 50000) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const done = (payload) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(payload);
    };
    s.waiters.push(done);
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      const idx = s.waiters.indexOf(done);
      if (idx >= 0) s.waiters.splice(idx, 1);
      reject(new Error('Steam login timeout'));
    }, timeoutMs);
  });
}

function setupClient(s) {
  const client = s.client;
  client.on('steamGuard', (domain, callback, lastCodeWrong) => {
    s.guardCallback = callback;
    s.state = 'await_guard';
    signal(s, {
      need: 'guard_code',
      session_id: String(s.id),
      bad_code: !!lastCodeWrong,
      domain: domain || ''
    });
  });
  client.on('loggedOn', () => {
    s.connected = true;
    s.state = s.running ? 'running' : 'connected';
    try {
      client.setPersona(s.hidden ? SteamUser.EPersonaState.Invisible : SteamUser.EPersonaState.Online);
    } catch (_) {}
    signal(s, {id: s.id, login: s.login});
  });
  client.on('error', (err) => {
    s.lastError = safeError(err);
    s.state = 'error';
    s.connected = false;
    signal(s, {error: s.lastError, eresult: err && err.eresult ? Number(err.eresult) : 0});
  });
  client.on('disconnected', (_eresult, msg) => {
    if (s.closing) return;
    s.connected = false;
    s.state = 'disconnected';
    if (msg) s.lastError = String(msg).slice(0, 300);
  });
}

async function createLogin(body) {
  const login = String(body.login || '').trim();
  const password = String(body.password || '');
  if (!login || !password) throw new Error('Login and password are required');
  const id = nextId++;
  const client = new SteamUser({autoRelogin: true, renewRefreshTokens: false, dataDirectory: null});
  const s = {
    id, login, client, hidden: !!body.hidden, state: 'connecting', connected: false,
    running: false, games: [], guardCallback: null, waiters: [], closing: false, lastError: ''
  };
  sessions.set(id, s);
  setupClient(s);
  const waiter = waitForSignal(s);
  client.logOn({accountName: login, password});
  const result = await waiter;
  if (result && result.error) {
    sessions.delete(id);
    try { client.logOff(); } catch (_) {}
  }
  return result;
}

async function submitGuard(id, code) {
  const s = sessions.get(Number(id));
  if (!s) return {error: 'Login session not found', code: 'login_expired'};
  if (typeof s.guardCallback !== 'function') return {error: 'Steam Guard is not waiting for a code', code: 'login_expired'};
  const waiter = waitForSignal(s);
  const callback = s.guardCallback;
  s.guardCallback = null;
  s.state = 'connecting';
  callback(String(code || '').trim());
  return await waiter;
}

function sendJson(res, status, payload) {
  const raw = Buffer.from(JSON.stringify(payload || {}));
  res.writeHead(status, {'Content-Type': 'application/json; charset=utf-8', 'Content-Length': raw.length});
  res.end(raw);
}

async function readJson(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 1024 * 1024) throw new Error('Request too large');
    chunks.push(chunk);
  }
  if (!chunks.length) return {};
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

async function route(req, res) {
  if (!TOKEN || req.headers.authorization !== `Bearer ${TOKEN}`) {
    return sendJson(res, 401, {error: 'unauthorized'});
  }
  const url = new URL(req.url, `http://${HOST}:${PORT}`);
  const path = url.pathname;
  if (req.method === 'GET' && path === '/health') {
    let version = '?';
    try { version = require('steam-user/package.json').version; } catch (_) {}
    return sendJson(res, 200, {ok: true, version, pid: process.pid, sessions: sessions.size});
  }
  if (req.method === 'GET' && path === '/sessions') {
    return sendJson(res, 200, {data: Array.from(sessions.values()).map(publicSession)});
  }
  if (req.method === 'POST' && path === '/login') {
    try {
      const result = await createLogin(await readJson(req));
      if (result && result.error) return sendJson(res, 400, result);
      return sendJson(res, 200, result || {});
    } catch (err) {
      return sendJson(res, 500, {error: safeError(err)});
    }
  }
  let match = path.match(/^\/sessions\/(\d+)\/guard$/);
  if (req.method === 'POST' && match) {
    try {
      const body = await readJson(req);
      const result = await submitGuard(match[1], body.code);
      if (result && result.code === 'login_expired') return sendJson(res, 404, result);
      return sendJson(res, 200, result || {});
    } catch (err) {
      return sendJson(res, 500, {error: safeError(err)});
    }
  }
  match = path.match(/^\/sessions\/(\d+)\/start$/);
  if (req.method === 'POST' && match) {
    const s = sessions.get(Number(match[1]));
    if (!s) return sendJson(res, 404, {error: 'Session not found'});
    try {
      const body = await readJson(req);
      const games = Array.from(new Set((Array.isArray(body.games) ? body.games : []).map(Number).filter(x => Number.isInteger(x) && x > 0))).slice(0, 32);
      if (!games.length) return sendJson(res, 400, {error: 'No games specified'});
      s.client.gamesPlayed(games);
      s.games = games;
      s.running = true;
      s.state = 'running';
      return sendJson(res, 200, publicSession(s));
    } catch (err) {
      return sendJson(res, 500, {error: safeError(err)});
    }
  }
  match = path.match(/^\/sessions\/(\d+)\/stop$/);
  if (req.method === 'POST' && match) {
    const s = sessions.get(Number(match[1]));
    if (!s) return sendJson(res, 404, {error: 'Session not found'});
    try {
      s.client.gamesPlayed([]);
      s.games = [];
      s.running = false;
      s.state = s.connected ? 'connected' : 'disconnected';
      return sendJson(res, 200, publicSession(s));
    } catch (err) {
      return sendJson(res, 500, {error: safeError(err)});
    }
  }
  match = path.match(/^\/sessions\/(\d+)$/);
  if (req.method === 'DELETE' && match) {
    const id = Number(match[1]);
    const s = sessions.get(id);
    if (!s) return sendJson(res, 200, {ok: true});
    s.closing = true;
    try { s.client.gamesPlayed([]); } catch (_) {}
    try { s.client.logOff(); } catch (_) {}
    sessions.delete(id);
    return sendJson(res, 200, {ok: true});
  }
  if (req.method === 'POST' && path === '/shutdown') {
    for (const s of sessions.values()) {
      s.closing = true;
      try { s.client.gamesPlayed([]); } catch (_) {}
      try { s.client.logOff(); } catch (_) {}
    }
    sessions.clear();
    sendJson(res, 200, {ok: true});
    setTimeout(() => process.exit(0), 100);
    return;
  }
  return sendJson(res, 404, {error: 'not_found'});
}

const server = http.createServer((req, res) => {
  route(req, res).catch(err => sendJson(res, 500, {error: safeError(err)}));
});
server.on('error', (err) => {
  console.error(`[steamfarm-helper] ${safeError(err)}`);
  process.exit(2);
});
server.listen(PORT, HOST, () => {
  console.log(`[steamfarm-helper] listening ${HOST}:${PORT}`);
});
"""
LOCAL_PACKAGE_SOURCE = json.dumps({
    'name': 'cardinal-steamfarm-local-helper',
    'private': True,
    'version': '1.0.0',
    'description': 'Runtime helper generated by Cardinal Steam Farm plugin',
    'dependencies': {'steam-user': LOCAL_STEAM_USER_VERSION},
}, ensure_ascii=False, indent=2)
def _write_local_helper_files(helper_path=None, package_path=None):
    helper = Path(helper_path or LOCAL_HELPER_FILE)
    package = Path(package_path or LOCAL_PACKAGE_FILE)
    helper.parent.mkdir(parents=True, exist_ok=True)
    package.parent.mkdir(parents=True, exist_ok=True)
    if not helper.is_file() or helper.read_text(encoding='utf-8', errors='ignore') != LOCAL_HELPER_SOURCE:
        helper.write_text(LOCAL_HELPER_SOURCE, encoding='utf-8')
    if not package.is_file() or package.read_text(encoding='utf-8', errors='ignore') != LOCAL_PACKAGE_SOURCE:
        package.write_text(LOCAL_PACKAGE_SOURCE, encoding='utf-8')
    return (str(helper), str(package))
def _local_meta():
    _ensure_dirs()
    data = _json_dict(LOCAL_META_FILE)
    token = str(data.get('token') or '').strip()
    if len(token) < 24:
        token = secrets.token_urlsafe(36)
        data['token'] = token
        _atomic_json(LOCAL_META_FILE, data)
        try:
            os.chmod(LOCAL_META_FILE, 0o600)
        except Exception:
            pass
    return {'token': token}
def _local_console(text):
    line = str(text or '').replace('\r', '').strip()
    if not line:
        return
    try:
        print(f'[steamfarm-local] {line}', flush=True)
    except Exception:
        pass
def _find_bundled_node(runtime_dir=None):
    root = Path(runtime_dir or LOCAL_RUNTIME_DIR)
    candidates = [root / 'node.exe', root / 'bin' / 'node']
    try:
        candidates.extend(sorted(root.glob('node-*/node.exe')))
        candidates.extend(sorted(root.glob('node-*/bin/node')))
    except Exception:
        pass
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    return ''
def _local_node_path():
    return _find_bundled_node() or shutil.which('node') or shutil.which('nodejs') or ''
def _node_version_for_path(node):
    if not node:
        return ''
    try:
        result = subprocess.run([str(node), '--version'], capture_output=True, text=True, timeout=5)
        return str(result.stdout or result.stderr or '').strip()[:80]
    except Exception:
        return ''
def _node_major_for_path(node):
    match = re.search(r'v?(\d+)', _node_version_for_path(node))
    return int(match.group(1)) if match else 0
def _node_asset_for_platform(system_name=None, machine_name=None):
    system_name = str(system_name or platform.system()).strip().lower()
    machine_name = str(machine_name or platform.machine()).strip().lower()
    if machine_name in {'amd64', 'x86_64', 'x64'}:
        arch = 'x64'
    elif machine_name in {'arm64', 'aarch64'}:
        arch = 'arm64'
    else:
        raise LocalFarmError('node_platform', f'Архитектура {machine_name or "?"} пока не поддерживается автоустановкой Node.js.')
    if system_name == 'windows':
        return (f'win-{arch}-zip', f'win-{arch}', '.zip')
    if system_name == 'linux':
        return (f'linux-{arch}', f'linux-{arch}', '.tar.xz')
    raise LocalFarmError('node_platform', f'Система {system_name or "?"} пока не поддерживается автоустановкой Node.js.')
def _select_node_lts_release(index_rows, file_key):
    for row in list(index_rows or []):
        if not isinstance(row, dict) or not row.get('lts'):
            continue
        files = row.get('files') or []
        if file_key in files and str(row.get('version') or '').startswith('v'):
            return str(row['version'])
    raise LocalFarmError('node_download_failed', f'Не удалось найти LTS Node.js для {file_key}.')
def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest().lower()
def _download_to_file(url, target, expected_sha256=''):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    _local_console(f'Скачивание: {url}')
    try:
        with requests.get(url, stream=True, timeout=(15, 60)) as response:
            response.raise_for_status()
            total = int(response.headers.get('Content-Length') or 0)
            done = 0
            next_report = 0
            with target.open('wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    if total > 0:
                        pct = int(done * 100 / total)
                        if pct >= next_report:
                            _local_console(f'Скачано Node.js: {pct}% ({done / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} МБ)')
                            next_report = min(100, pct + 10)
                    elif done // (5 * 1024 * 1024) > (done - len(chunk)) // (5 * 1024 * 1024):
                        _local_console(f'Скачано Node.js: {done / 1024 / 1024:.1f} МБ')
    except Exception as e:
        try:
            target.unlink(missing_ok=True)
        except Exception:
            pass
        raise LocalFarmError('node_download_failed', f'Не удалось скачать Node.js: {e}') from e
    if expected_sha256:
        actual = _sha256_file(target)
        if actual != str(expected_sha256).strip().lower():
            try:
                target.unlink(missing_ok=True)
            except Exception:
                pass
            raise LocalFarmError('node_download_failed', 'Контрольная сумма скачанного Node.js не совпала.')
    return str(target)
def _ensure_local_node_runtime():
    existing = _local_node_path()
    if existing and _node_major_for_path(existing) >= 14:
        _local_console(f'Node.js найден: {existing} ({_node_version_for_path(existing)})')
        return existing
    if existing:
        _local_console(f'Найден слишком старый/нерабочий Node.js: {existing} ({_node_version_for_path(existing) or "версия не определена"}).')
    _local_console('Устанавливаю portable Node.js LTS автоматически.')
    file_key, platform_tag, ext = _node_asset_for_platform()
    try:
        index_response = requests.get(f'{LOCAL_NODE_DIST}/index.json', timeout=(15, 30))
        index_response.raise_for_status()
        version = _select_node_lts_release(index_response.json(), file_key)
        sums_response = requests.get(f'{LOCAL_NODE_DIST}/{version}/SHASUMS256.txt', timeout=(15, 30))
        sums_response.raise_for_status()
    except LocalFarmError:
        raise
    except Exception as e:
        raise LocalFarmError('node_download_failed', f'Не удалось получить список Node.js: {e}') from e
    filename = f'node-{version}-{platform_tag}{ext}'
    expected = ''
    for line in str(sums_response.text or '').splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[-1].lstrip('*') == filename:
            expected = parts[0].strip().lower()
            break
    if not expected:
        raise LocalFarmError('node_download_failed', f'Для {filename} не найдена контрольная сумма Node.js.')
    runtime = Path(LOCAL_RUNTIME_DIR)
    runtime.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='steamfarm-node-', dir=str(runtime.parent)) as td:
        temp = Path(td)
        archive = temp / filename
        _download_to_file(f'{LOCAL_NODE_DIST}/{version}/{filename}', archive, expected)
        unpacked = temp / 'unpacked'
        unpacked.mkdir(parents=True, exist_ok=True)
        _local_console('Распаковываю Node.js...')
        try:
            if ext == '.zip':
                with zipfile.ZipFile(archive, 'r') as zf:
                    zf.extractall(unpacked)
            else:
                with tarfile.open(archive, 'r:xz') as tf:
                    tf.extractall(unpacked)
        except Exception as e:
            raise LocalFarmError('node_download_failed', f'Не удалось распаковать Node.js: {e}') from e
        roots = [x for x in unpacked.iterdir() if x.is_dir()]
        source = roots[0] if len(roots) == 1 else unpacked
        replacement = temp / 'runtime-new'
        shutil.copytree(source, replacement)
        if runtime.exists():
            shutil.rmtree(runtime, ignore_errors=True)
        shutil.move(str(replacement), str(runtime))
    node = _find_bundled_node(runtime)
    if not node:
        raise LocalFarmError('node_download_failed', 'Node.js скачан, но node/node.exe после распаковки не найден.')
    if os.name != 'nt':
        try:
            os.chmod(node, os.stat(node).st_mode | 0o111)
        except Exception:
            pass
    _local_console(f'Portable Node.js {version} установлен: {node}')
    return node
def _local_npm_candidates(node, windows=None):
    if not node:
        return []
    base = Path(node).resolve().parent
    is_windows = (os.name == 'nt') if windows is None else bool(windows)
    if is_windows:
        return [str(base / 'npm.cmd'), str(base / 'npm.exe')]
    return [str(base / 'npm'), str(base / 'npm.cmd'), str(base / 'npm.exe')]
def _local_npm_path():
    node = _local_node_path()
    for candidate in _local_npm_candidates(node):
        if Path(candidate).is_file():
            return str(candidate)
    if os.name == 'nt':
        return shutil.which('npm.cmd') or shutil.which('npm.exe') or ''
    return shutil.which('npm') or shutil.which('npm.cmd') or ''
def _local_dependency_ready():
    return (Path(LOCAL_DIR) / 'node_modules' / 'steam-user' / 'package.json').is_file()
def _local_npm_install_command(npm):
    return [
        str(npm), 'install', '--omit=dev', '--no-audit', '--no-fund',
        '--loglevel=http', '--fetch-retries=4',
        '--fetch-retry-mintimeout=2000', '--fetch-retry-maxtimeout=20000',
    ]
def _local_node_version():
    return _node_version_for_path(_local_node_path())
def _install_local_runtime():
    _ensure_dirs()
    _write_local_helper_files()
    _local_console('=== Установка Local backend начата ===')
    node = _ensure_local_node_runtime()
    npm = _local_npm_path()
    _local_console(f'Node.js: {node} ({_local_node_version() or "версия не определена"})')
    if not npm:
        raise LocalFarmError('npm_missing', 'npm не найден рядом с Node.js.')
    _local_console(f'npm: {npm}')
    cmd = _local_npm_install_command(npm)
    _local_console('Запускаю npm install steam-user. Весь вывод npm будет ниже в терминале Cardinal.')
    started = time.monotonic()
    creationflags = int(getattr(subprocess, 'CREATE_NO_WINDOW', 0) or 0) if os.name == 'nt' else 0
    env = os.environ.copy()
    node_dir = str(Path(node).resolve().parent)
    env['PATH'] = node_dir + os.pathsep + str(env.get('PATH') or '')
    try:
        proc = subprocess.Popen(
            cmd, cwd=LOCAL_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='replace', bufsize=1,
            creationflags=creationflags, env=env,
        )
    except Exception as e:
        raise LocalFarmError('install_failed', f'Не удалось запустить npm: {e}') from e
    output = []
    try:
        stream = getattr(proc, 'stdout', None)
        if stream is not None:
            for raw in iter(stream.readline, ''):
                line = str(raw or '').rstrip()
                if line:
                    output.append(line)
                    output = output[-200:]
                    _local_console(line)
                if time.monotonic() - started > 600:
                    proc.kill()
                    raise LocalFarmError('install_timeout', 'Установка steam-user не завершилась за 10 минут.')
        returncode = proc.wait(timeout=10)
    except LocalFarmError:
        raise
    except subprocess.TimeoutExpired as e:
        try:
            proc.kill()
        except Exception:
            pass
        raise LocalFarmError('install_timeout', 'Установка steam-user зависла.') from e
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        raise LocalFarmError('install_failed', f'Ошибка чтения npm: {e}') from e
    finally:
        try:
            if getattr(proc, 'stdout', None):
                proc.stdout.close()
        except Exception:
            pass
    _local_console(f'npm завершён с кодом {int(returncode)}.')
    if int(returncode) != 0 or not _local_dependency_ready():
        text = '\n'.join(output[-30:]).strip() or 'npm install failed'
        raise LocalFarmError('install_failed', text[-2400:])
    _local_console('steam-user установлен. === Установка Local backend завершена ===')
    return {'ok': True, 'node': node, 'npm': npm, 'version': _local_node_version()}
def _local_base_url():
    return f"http://127.0.0.1:{int(cfg_get('local_port') or LOCAL_DEFAULT_PORT)}"
def _local_direct_request(method, path, body=None, timeout=5):
    token = _local_meta()['token']
    r = requests.request(method, _local_base_url() + path, json=body, headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'}, timeout=timeout)
    try:
        payload = r.json()
    except Exception:
        payload = {}
    if not (200 <= int(r.status_code) < 300):
        if isinstance(payload, dict):
            message = str(payload.get('error') or getattr(r, 'text', '') or f'HTTP {r.status_code}')[:400]
            code = str(payload.get('code') or f'http_{r.status_code}')
            extra = payload
        else:
            message = str(getattr(r, 'text', '') or f'HTTP {r.status_code}')[:400]
            code = f'http_{r.status_code}'
            extra = {}
        raise LocalFarmError(code, message, extra)
    return payload if isinstance(payload, dict) else {'data': payload}
def _local_daemon_alive():
    if not _local_dependency_ready():
        return False
    try:
        return bool(_local_direct_request('GET', '/health', timeout=1.2).get('ok'))
    except Exception:
        return False
def _local_daemon_log_tail(path=None, max_lines=20, max_chars=1800):
    target = Path(path or LOCAL_DAEMON_LOG)
    if not target.is_file():
        return ''
    try:
        text = '\n'.join(target.read_text(encoding='utf-8', errors='replace').splitlines()[-max_lines:])
        return text[-max_chars:].strip()
    except Exception:
        return ''
def _local_daemon_exit_reason(proc, log_path=None):
    code = proc.poll() if proc is not None else None
    if code is None:
        return ''
    tail = _local_daemon_log_tail(log_path)
    base = f'Node helper завершился, код {code}.'
    return (base + (f' {tail}' if tail else '')).strip()
def _local_helper_launch_command(node, helper_path=None):
    helper = Path(helper_path or LOCAL_HELPER_FILE).resolve()
    return [str(node), str(helper)]
def _start_local_daemon(force=False):
    global _local_process
    _write_local_helper_files()
    if not _local_dependency_ready():
        raise LocalFarmError('not_installed', 'Local backend ещё не установлен. Нажмите «Установить / обновить».')
    if force and _local_daemon_alive():
        _stop_local_daemon()
    with _local_process_lock:
        if not force and _local_daemon_alive():
            return _local_direct_request('GET', '/health', timeout=2)
        node = _ensure_local_node_runtime()
        env = os.environ.copy()
        env['STEAMFARM_PORT'] = str(int(cfg_get('local_port') or LOCAL_DEFAULT_PORT))
        env['STEAMFARM_TOKEN'] = _local_meta()['token']
        Path(LOCAL_DAEMON_LOG).parent.mkdir(parents=True, exist_ok=True)
        log = open(LOCAL_DAEMON_LOG, 'wb', buffering=0)
        local_cwd = str(Path(LOCAL_DIR).resolve())
        launch_cmd = _local_helper_launch_command(node)
        kwargs = {'cwd': local_cwd, 'env': env, 'stdin': subprocess.DEVNULL, 'stdout': log, 'stderr': subprocess.STDOUT}
        if os.name == 'nt':
            kwargs['creationflags'] = int(getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)) | int(getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        else:
            kwargs['start_new_session'] = True
        try:
            _local_console('Запускаю Local helper: ' + ' '.join(launch_cmd))
            _local_process = subprocess.Popen(launch_cmd, **kwargs)
        except Exception as e:
            raise LocalFarmError('start_failed', str(e)) from e
        finally:
            try:
                log.close()
            except Exception:
                pass
    deadline = time.monotonic() + 12
    last = ''
    while time.monotonic() < deadline:
        reason = _local_daemon_exit_reason(_local_process)
        if reason:
            _local_console(reason)
            raise LocalFarmError('start_failed', reason)
        try:
            health = _local_direct_request('GET', '/health', timeout=0.7)
            if health.get('ok'):
                _local_console(f'Local helper готов: 127.0.0.1:{int(cfg_get("local_port") or LOCAL_DEFAULT_PORT)}')
                return health
        except Exception as e:
            last = str(e)
        time.sleep(0.25)
    tail = _local_daemon_log_tail()
    details = tail or last or 'процесс запущен, но /health не ответил'
    _local_console(f'Local helper не запустился: {details}')
    raise LocalFarmError('start_failed', f'Local helper не ответил за 12 сек. {details}')
def _stop_local_daemon():
    global _local_process
    try:
        _local_direct_request('POST', '/shutdown', {}, timeout=3)
    except Exception:
        pass
    with _local_process_lock:
        proc = _local_process
        _local_process = None
    if proc is not None:
        try:
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
    return True
def _local_runtime_status(live=True):
    _write_local_helper_files()
    node = _local_node_path()
    if node and _node_major_for_path(node) < 14:
        node = ''
    npm = _local_npm_path() if node else ''
    installed = _local_dependency_ready()
    health = None
    error = ''
    if live and installed and node:
        try:
            if _local_daemon_alive():
                health = _local_direct_request('GET', '/health', timeout=2)
        except Exception as e:
            error = _human_error(e)
    accounts = []
    if health:
        try:
            accounts = list(_local_direct_request('GET', '/sessions', timeout=3).get('data') or [])
        except Exception:
            accounts = []
    return {'node': node, 'npm': npm, 'node_version': _local_node_version() if node else '', 'installed': installed, 'health': health, 'accounts': accounts, 'error': error}
class LocalFarmClient:
    def _request(self, method, path, body=None, timeout=60):
        if not _local_daemon_alive():
            _start_local_daemon()
        return _local_direct_request(method, path, body=body, timeout=timeout)
    def ping(self):
        return self._request('GET', '/health', timeout=5)
    def get_balance_kop(self):
        return 0
    def get_plans(self):
        return []
    def get_subscription(self):
        return _local_subscription_snapshot()
    def get_accounts(self):
        data = self._request('GET', '/sessions', timeout=10).get('data')
        rows = [dict(x) for x in data] if isinstance(data, list) else []
        return [x for x in rows if bool(x.get('connected')) or str(x.get('state') or '') in {'connected', 'running'}]
    def login_account(self, login, password, games, hidden):
        try:
            result = self._request('POST', '/login', {'login': str(login), 'password': str(password), 'hidden': bool(hidden)}, timeout=60)
        except LocalFarmError as e:
            if e.code.startswith('http_4'):
                raise LocalFarmError('steam_login_failed', e.message, e.extra) from e
            raise
        if str(result.get('need') or '') == 'guard_code':
            return result
        if not int(result.get('id') or 0):
            raise LocalFarmError('steam_login_failed', str(result.get('error') or 'Steam не подтвердил вход.'))
        return result
    def submit_guard_code(self, session_id, code):
        try:
            result = self._request('POST', f'/sessions/{int(session_id)}/guard', {'code': str(code)}, timeout=60)
        except LocalFarmError as e:
            if e.code in ('login_expired', 'http_404'):
                raise LocalFarmError('login_expired', 'Сессия входа устарела.', e.extra) from e
            raise
        if str(result.get('need') or '') == 'guard_code':
            if bool(result.get('bad_code')):
                raise LocalFarmError('bad_code', 'Код Steam Guard не подошёл.', result)
            return result
        if not int(result.get('id') or 0):
            raise LocalFarmError('steam_login_failed', str(result.get('error') or 'Steam не подтвердил вход.'))
        return result
    def patch_account(self, account_id, games=None, running=None, mode=None, hidden=None):
        account_id = int(account_id)
        if running is False:
            return self._request('POST', f'/sessions/{account_id}/stop', {}, timeout=15)
        if running is True:
            selected = [int(x) for x in list(games or [])][:32]
            if not selected:
                raise LocalFarmError('invalid_request', 'Для запуска Local нужно указать хотя бы одну игру.')
            return self._request('POST', f'/sessions/{account_id}/start', {'games': selected, 'hidden': bool(hidden)}, timeout=15)
        if games is not None:
            return self._request('POST', f'/sessions/{account_id}/start', {'games': [int(x) for x in games][:32], 'hidden': bool(hidden)}, timeout=15)
        return {'ok': True}
    def delete_account(self, account_id):
        return self._request('DELETE', f'/sessions/{int(account_id)}', timeout=15)
class FarmClient:
    def __init__(self, api_key, base_url=BASE_URL):
        self.api_key = str(api_key or '').strip()
        self.base_url = str(base_url or BASE_URL).rstrip('/')
    def _request(self, method, path, body=None, params=None, idem_key=None, timeout=30, attempts=3):
        headers = {'Accept': 'application/json', 'User-Agent': f'dim4n4ik-steam-farm-cardinal/{VERSION}'}
        if path != '/v1/ping':
            headers['Authorization'] = f'Bearer {self.api_key}'
        if body is not None:
            headers['Content-Type'] = 'application/json'
        if idem_key:
            headers['Idempotency-Key'] = str(idem_key)
        last = None
        for attempt in range(1, max(1, int(attempts)) + 1):
            started = time.monotonic()
            try:
                r = requests.request(method, self.base_url + path, json=body, params=params, headers=headers, timeout=timeout)
            except requests.RequestException as e:
                last = e
                _log_event('api_network_error', level=logging.WARNING, method=method, path=path, attempt=attempt, error=type(e).__name__)
                if attempt < attempts:
                    time.sleep(min(attempt * 1.5, 4))
                    continue
                raise FarmNetworkError(str(e))
            _log_event('api_request', method=method, path=path, status=r.status_code, attempt=attempt, ms=int((time.monotonic() - started) * 1000))
            if 200 <= int(r.status_code) < 300:
                try:
                    data = r.json()
                except Exception as e:
                    raise FarmApiError(r.status_code, 'bad_json', 'Сервис вернул некорректный JSON') from e
                return data if isinstance(data, dict) else {'data': data}
            try:
                payload = r.json()
                err = payload.get('error') if isinstance(payload, dict) and isinstance(payload.get('error'), dict) else {}
            except Exception:
                err = {}
            code = str(err.get('code') or f'http_{r.status_code}')
            message = str(err.get('message') or getattr(r, 'text', '') or code)[:300]
            if r.status_code == 429 and attempt < attempts:
                try:
                    wait = max(1, min(15, int(r.headers.get('Retry-After', '2'))))
                except Exception:
                    wait = 2
                time.sleep(wait)
                continue
            if r.status_code >= 500 and attempt < attempts:
                time.sleep(min(attempt * 1.5, 4))
                continue
            raise FarmApiError(r.status_code, code, message, err)
        raise FarmNetworkError(str(last or 'Не удалось выполнить запрос'))
    def ping(self):
        return self._request('GET', '/v1/ping', timeout=15, attempts=2)
    def get_balance_kop(self):
        return int(self._request('GET', '/v1/balance').get('balance_kop', 0) or 0)
    def get_plans(self):
        d = self._request('GET', '/v1/farm/plans').get('data')
        return d if isinstance(d, list) else []
    def get_subscription(self):
        return self._request('GET', '/v1/farm/subscription')
    def buy_subscription(self, plan, months, accounts, idem_key):
        return self._request('POST', '/v1/farm/subscription', body={'plan': str(plan), 'months': int(months), 'accounts': int(accounts)}, idem_key=idem_key, timeout=60)
    def get_accounts(self):
        d = self._request('GET', '/v1/farm/accounts').get('data')
        return d if isinstance(d, list) else []
    def login_account(self, login, password, games, hidden):
        return self._request('POST', '/v1/farm/accounts/login', body={'login': str(login), 'password': str(password), 'games': [int(x) for x in games], 'hidden': bool(hidden)}, timeout=60, attempts=2)
    def submit_guard_code(self, session_id, code):
        return self._request('POST', f'/v1/farm/accounts/login/{str(session_id)}/code', body={'code': str(code)}, timeout=60, attempts=2)
    def patch_account(self, account_id, games=None, running=None, mode=None, hidden=None):
        body = {}
        if games is not None:
            body['games'] = [int(x) for x in games]
        if running is not None:
            body['running'] = bool(running)
        if mode is not None:
            body['mode'] = str(mode)
        if hidden is not None:
            body['hidden'] = bool(hidden)
        if not body:
            raise ValueError('Не указаны изменения аккаунта')
        return self._request('PATCH', f'/v1/farm/accounts/{int(account_id)}', body=body)
    def delete_account(self, account_id):
        return self._request('DELETE', f'/v1/farm/accounts/{int(account_id)}')
def _get_api_client():
    global _client
    key = str(cfg_get('api_key') or '').strip()
    if not key:
        return None
    if _client is None or _client.api_key != key:
        _client = FarmClient(key)
    return _client
def _get_client():
    global _local_client
    if _backend_mode() == 'local':
        if _local_client is None:
            _local_client = LocalFarmClient()
        return _local_client
    return _get_api_client()
def _invalidate_snapshot():
    with _snapshot_lock:
        _snapshot_cache.update({'ts': 0.0, 'sub': None, 'accounts': None})
def _api_snapshot(force=False, max_age=4.0):
    client = _get_client()
    if client is None:
        raise ValueError('API-ключ не задан' if _backend_mode() == 'api' else 'Local backend недоступен')
    now = time.time()
    with _snapshot_lock:
        if not force and _snapshot_cache['sub'] is not None and (_snapshot_cache['accounts'] is not None) and (now - float(_snapshot_cache['ts'] or 0) <= max_age):
            return {'subscription': dict(_snapshot_cache['sub']), 'accounts': [dict(x) for x in _snapshot_cache['accounts']]}
    sub = client.get_subscription()
    accounts = client.get_accounts()
    rows = [dict(x) for x in accounts if isinstance(x, dict)]
    with _snapshot_lock:
        _snapshot_cache.update({'ts': now, 'sub': dict(sub or {}), 'accounts': rows})
    return {'subscription': dict(sub or {}), 'accounts': [dict(x) for x in rows]}
def _human_error(e):
    if isinstance(e, FarmApiError):
        base = ERROR_HUMAN.get(e.code, e.message or e.code)
        if e.code == 'insufficient_balance' and e.extra.get('need_kop') is not None:
            return f"{base} Не хватает: {_fmt_rub(e.extra.get('need_kop'))}."
        return base
    if isinstance(e, LocalFarmError):
        mapping = {'node_missing': 'Node.js не найден.', 'node_platform': 'Автоустановка Node.js не поддерживает эту платформу.', 'node_download_failed': 'Не удалось автоматически установить Node.js.', 'npm_missing': 'npm не найден.', 'not_installed': 'Local backend ещё не установлен.', 'bad_code': 'Код Steam Guard не подошёл.', 'login_expired': 'Сессия входа устарела.', 'steam_login_failed': 'Steam не принял вход.', 'start_failed': 'Не удалось запустить Local helper.', 'install_failed': 'Не удалось установить Local backend.', 'install_timeout': 'Установка Local backend превысила лимит времени.'}
        message = str(e.message or '')
        low = message.lower()
        if e.code in {'install_failed', 'install_timeout'} and any(x in low for x in ('econnreset', 'etimedout', 'eai_again', 'enotfound', 'network request', 'network connectivity')):
            return 'Сетевая ошибка npm: соединение с registry.npmjs.org было прервано или недоступно. Повторите установку; подробный вывод смотрите в терминале Cardinal.'
        base = mapping.get(e.code, '')
        return (base + ((' ' + message) if message and message not in base else '')).strip()[:500]
    if isinstance(e, FarmNetworkError):
        return 'Не удалось подключиться к API. Проверьте доступность сервиса и интернет.'
    return str(e)[:250]
def _fmt_rub(kop):
    try:
        return f'{int(kop) / 100:.2f}'.rstrip('0').rstrip('.') + ' ₽'
    except Exception:
        return '—'
def _mask_key(key):
    key = str(key or '')
    return '❌ не задан' if not key else f'rk_...{key[-4:]}' if len(key) > 4 else 'rk_***'
def _normalize_appids(values, limit=32):
    raw = values if isinstance(values, (list, tuple, set)) else re.findall('\\d+', str(values or ''))
    result = []
    seen = set()
    for x in raw:
        try:
            v = int(x)
        except Exception:
            continue
        if v <= 0 or v in seen:
            continue
        seen.add(v)
        result.append(v)
        if len(result) >= max(1, int(limit)):
            break
    return result
def _parse_api_datetime(value):
    text = str(value or '').strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp()
    except Exception:
        pass
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
        try:
            return time.mktime(datetime.strptime(text, fmt).timetuple())
        except Exception:
            pass
    return None
def _format_duration(seconds):
    total = max(0, int(seconds or 0))
    h, rem = divmod(total, 3600)
    m, _ = divmod(rem, 60)
    return f'{h} ч {m} мин' if h else f'{m} мин'
def _is_authorized(user_id):
    try:
        auth = getattr(getattr(cardinal, 'telegram', None), 'authorized_users', None)
        if isinstance(auth, dict):
            return user_id in auth or int(user_id) in auth
    except Exception:
        pass
    return True
def _make_kb(rows):
    if not tg_types:
        return None
    kb = tg_types.InlineKeyboardMarkup()
    for row in rows:
        btn = []
        for text, target in row:
            btn.append(tg_types.InlineKeyboardButton(text, url=target) if str(target).startswith(('http://', 'https://')) else tg_types.InlineKeyboardButton(text, callback_data=target))
        kb.row(*btn)
    return kb
def _tg_send(chat_id, text, kb=None):
    if not bot or not chat_id:
        return
    try:
        bot.send_message(int(chat_id), text, parse_mode='HTML', reply_markup=kb, disable_web_page_preview=True)
    except Exception as e:
        _log_event('telegram_send_error', level=logging.WARNING, error=str(e))
def _tg_edit(chat_id, message_id, text, kb=None):
    if not message_id:
        _tg_send(chat_id, text, kb)
        return
    try:
        bot.edit_message_text(text, int(chat_id), int(message_id), parse_mode='HTML', reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        _tg_send(chat_id, text, kb)
def _send_document(chat_id, path, caption=''):
    if not bot or not Path(path).is_file():
        return False
    try:
        with open(path, 'rb') as f:
            bot.send_document(int(chat_id), f, caption=caption or None, parse_mode='HTML')
        return True
    except Exception as e:
        _log_event('send_document_error', level=logging.WARNING, error=str(e))
        return False
def _delete_user_message(message):
    if not bot:
        return
    try:
        cid = getattr(getattr(message, 'chat', None), 'id', None)
        mid = getattr(message, 'message_id', None)
        if cid and mid:
            bot.delete_message(int(cid), int(mid))
    except Exception:
        pass
def _ack(call, text=None):
    try:
        bot.answer_callback_query(call.id, text)
    except Exception:
        pass
def _fp_send(chat_id, text, buyer_username=None):
    if cardinal is None or getattr(cardinal, 'account', None) is None:
        return False
    try:
        cid = int(chat_id)
    except Exception:
        cid = None
    if cid is None and buyer_username:
        try:
            chat = cardinal.account.get_chat_by_name(str(buyer_username), True)
            cid = int(getattr(chat, 'id', 0) or 0) if chat else None
        except Exception:
            cid = None
    if cid is None:
        return False
    plain = html.unescape(re.sub('</?(?:b|code)>', '', str(text), flags=re.I))
    for attempt in range(3):
        try:
            cardinal.account.send_message(cid, plain)
            return True
        except Exception as e:
            _log_event('funpay_send_error', level=logging.WARNING, attempt=attempt + 1, error=str(e))
            time.sleep(0.5 + attempt * 0.5)
    return False
def _safe_format(template, values):
    class Safe(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    return str(template or '').format_map(Safe({k: str(v) for k, v in values.items()}))
def _buyer_message(key, **values):
    configured = cfg_get('messages')
    template = (configured.get(key) if isinstance(configured, dict) else None) or DEFAULT_MESSAGES.get(key, '')
    return _safe_format(template, values)
def _validate_message_template(text):
    text = str(text or '').strip()
    if not text:
        raise ValueError('Сообщение не может быть пустым')
    if len(text) > 3000:
        raise ValueError('Сообщение слишком длинное')
    fields = set(re.findall('{([A-Za-z_][A-Za-z0-9_]*)}', text))
    unknown = fields - MESSAGE_FIELDS
    if unknown:
        raise ValueError('Неизвестные переменные: ' + ', '.join(sorted(unknown)))
    try:
        _safe_format(text, {x: 'test' for x in MESSAGE_FIELDS})
    except Exception as e:
        raise ValueError(f'Ошибка шаблона: {e}')
    return text
def _notify_admin(text, keyboard=None, etype=None):
    if not bool(cfg_get('notifications_enabled')):
        return
    mapping = {'new_order': 'notify_new_order', 'started': 'notify_started', 'completed': 'notify_completed', 'error': 'notify_errors', 'subscription': 'notify_subscription', 'capacity': 'notify_capacity', 'reconnect': 'notify_reconnect'}
    key = mapping.get(str(etype or ''))
    if key and (not bool(cfg_get(key))):
        return
    if admin_chat_id:
        _tg_send(int(admin_chat_id), text, keyboard)
def _normalize_binding(raw):
    b = dict(raw or {})
    try:
        hours = max(0.25, min(720.0, float(b.get('hours_per_unit', 1) or 1)))
    except Exception:
        hours = 1.0
    try:
        max_games = max(1, min(32, int(b.get('max_games', 1) or 1)))
    except Exception:
        max_games = 1
    policy = str(b.get('game_policy') or 'buyer').lower()
    if policy not in ('buyer', 'fixed'):
        policy = 'buyer'
    fixed = _normalize_appids(b.get('fixed_games') or [], max_games)
    if policy == 'fixed' and (not fixed):
        policy = 'buyer'
    manual = bool(b.get('manual_disabled', False))
    return {'lot_id': str(b.get('lot_id') or ''), 'lot_name': str(b.get('lot_name') or ''), 'hours_per_unit': hours, 'max_games': max_games, 'hidden': bool(b.get('hidden', False)), 'game_policy': policy, 'fixed_games': fixed, 'enabled': bool(b.get('enabled', True)) and (not manual), 'manual_disabled': manual, 'created_at': b.get('created_at') or int(time.time())}
def _safe_service_for_save(service):
    blocked = {'password', 'guard_code', 'steam_password', 'session_id'}
    return {str(k): v for k, v in dict(service or {}).items() if str(k).lower() not in blocked}
def _save_runtime_state():
    with _state_lock:
        _atomic_json(BINDINGS_FILE, {str(k): _normalize_binding(v) for k, v in _bindings.items() if isinstance(v, dict)})
        _atomic_json(SERVICES_FILE, {str(k): _safe_service_for_save(v) for k, v in _services.items() if isinstance(v, dict)})
        _atomic_json(AUTO_DISABLED_FILE, dict(_auto_disabled))
        _atomic_json(NOTIFY_STATE_FILE, dict(_notify_state))
def _service_duration_hours(binding, quantity):
    try:
        qty = max(1, int(quantity or 1))
    except Exception:
        qty = 1
    return float(_normalize_binding(binding)['hours_per_unit']) * qty
def _slot_reservation_count(now_ts=None):
    now = float(now_ts if now_ts is not None else time.time())
    count = 0
    with _state_lock:
        rows = [dict(v) for v in _services.values() if isinstance(v, dict)]
    for service in rows:
        if str(service.get('step') or '') not in {'await_password', 'await_guard'}:
            continue
        try:
            if int(service.get('api_account_id') or 0) > 0:
                continue
        except Exception:
            pass
        try:
            stamp = float(service.get('slot_reserved_at') or 0)
        except Exception:
            stamp = 0
        if stamp > 0 and now - stamp <= SLOT_RESERVATION_TTL_SEC:
            count += 1
    return count
def _occupied_account_count(accounts=None, now_ts=None):
    rows = [x for x in list(accounts or []) if isinstance(x, dict)]
    ids = set()
    for account in rows:
        try:
            aid = int(account.get('id') or 0)
            if aid > 0:
                ids.add(aid)
        except Exception:
            pass
    occupied = len(rows)
    final = {'completed', 'stopped_manual', 'disconnected', 'refunded'}
    with _state_lock:
        services = [dict(v) for v in _services.values() if isinstance(v, dict)]
    for service in services:
        if str(service.get('step') or '') in final:
            continue
        try:
            aid = int(service.get('api_account_id') or 0)
        except Exception:
            aid = 0
        if aid > 0 and aid not in ids:
            ids.add(aid)
            occupied += 1
    return occupied + _slot_reservation_count(now_ts)
def _capacity_slot_snapshot(subscription, accounts=None, now_ts=None):
    rows = [x for x in list(accounts or []) if isinstance(x, dict)]
    try:
        limit = max(0, int((subscription or {}).get('accounts', 0) or 0))
    except Exception:
        limit = 0
    reserved = _slot_reservation_count(now_ts)
    occupied = _occupied_account_count(rows, now_ts)
    return {'limit': limit, 'api_accounts': len(rows), 'reserved': reserved, 'occupied': occupied, 'free': max(0, limit - occupied)}
def _safe_subscription_hours(subscription, now_ts=None):
    sub = dict(subscription or {})
    now = float(now_ts if now_ts is not None else time.time())
    if str(sub.get('backend') or '').lower() == 'local':
        return (1000000000.0, '')
    if not bool(sub.get('active')):
        return (0.0, 'no_subscription')
    expires = _parse_api_datetime(sub.get('expires_at'))
    if not expires:
        return (0.0, 'bad_expiry')
    try:
        buffer = max(0.0, min(24.0, float(cfg_get('safety_buffer_hours') or 1)))
    except Exception:
        buffer = 1.0
    return (max(0.0, (expires - now) / 3600.0 - buffer), '')
def _queue_start_delay_hours(subscription, now_ts=None):
    now = float(now_ts if now_ts is not None else time.time())
    try:
        slots = max(1, int((subscription or {}).get('accounts', 0) or 0))
    except Exception:
        slots = 1
    loads = []
    queued = []
    with _state_lock:
        rows = [dict(v) for v in _services.values() if isinstance(v, dict)]
    for service in rows:
        step = str(service.get('step') or '')
        try:
            duration = max(0.0, float(service.get('duration_hours') or 0))
        except Exception:
            duration = 0
        if step in ('running', 'stop_retry'):
            try:
                remaining = max(0.0, (float(service.get('ends_at') or 0) - now) / 3600.0)
            except Exception:
                remaining = duration
            loads.append(remaining if remaining > 0 else duration)
        elif step in ('await_password', 'await_guard', 'await_games'):
            loads.append(duration)
        elif step == 'queued':
            queued.append((float(service.get('created_at', 0) or 0), duration))
    loads = sorted(loads, reverse=True)[:slots]
    while len(loads) < slots:
        loads.append(0.0)
    for _, duration in sorted(queued, key=lambda x: x[0]):
        idx = min(range(len(loads)), key=lambda i: loads[i])
        loads[idx] += duration
    return min(loads) if loads else 0.0
def _capacity_for_binding(binding, subscription, connected_count, now_ts=None):
    b = _normalize_binding(binding)
    sub = dict(subscription or {})
    safe, reason = _safe_subscription_hours(sub, now_ts)
    if reason:
        return {'ok': False, 'sellable_qty': 0, 'reason': reason, 'safe_hours': safe}
    try:
        limit = max(0, int(sub.get('accounts', 0) or 0))
        game_limit = max(0, int(sub.get('games', 0) or 0))
    except Exception:
        limit = game_limit = 0
    if b['max_games'] > game_limit or (b['game_policy'] == 'fixed' and len(b['fixed_games']) > game_limit):
        return {'ok': False, 'sellable_qty': 0, 'reason': 'games_over_plan', 'safe_hours': safe}
    if limit <= 0 or (int(connected_count or 0) >= limit and (not bool(cfg_get('queue_enabled')))):
        return {'ok': False, 'sellable_qty': 0, 'reason': 'no_free_slots', 'safe_hours': safe}
    delay = _queue_start_delay_hours(sub, now_ts) if bool(cfg_get('queue_enabled')) else 0.0
    if str(sub.get('backend') or '').lower() == 'local':
        qty = 999
        return {'ok': True, 'sellable_qty': qty, 'reason': '', 'safe_hours': safe, 'queue_delay_hours': delay}
    available = max(0.0, safe - delay)
    qty = int(available // b['hours_per_unit']) if b['hours_per_unit'] > 0 else 0
    return {'ok': qty > 0, 'sellable_qty': max(0, qty), 'reason': '' if qty > 0 else 'not_enough_time', 'safe_hours': safe, 'queue_delay_hours': delay}
def _capacity_reason_text(reason):
    return {'no_api_key': 'API-ключ не настроен.', 'no_subscription': 'Нет активной подписки на фарм.', 'bad_expiry': 'Не удалось определить срок подписки.', 'no_free_slots': 'На тарифе нет свободного места для нового Steam-аккаунта.', 'games_over_plan': 'Лимит игр этого лота превышает текущий тариф.', 'not_enough_time': 'До окончания подписки недостаточно безопасного времени.', 'api_error': 'Не удалось проверить состояние API.', 'backend_error': 'Не удалось проверить состояние выбранного движка фарма.', 'queued_fifo': 'Перед этим заказом уже есть более ранние заказы в очереди.', 'queued_no_free_slots': 'Сейчас все места заняты, заказ будет поставлен в очередь.'}.get(str(reason or ''), 'Заказ сейчас нельзя безопасно запустить.')
def _set_funpay_lot_fields(lot_id, active=None, amount=None, attempts=3):
    if cardinal is None or getattr(cardinal, 'account', None) is None:
        return False
    for attempt in range(1, max(1, int(attempts)) + 1):
        try:
            lf = cardinal.account.get_lot_fields(int(lot_id))
            changed = False
            if bool(getattr(lf, 'auto_delivery', False)):
                lf.auto_delivery = False
                changed = True
            if list(getattr(lf, 'secrets', None) or []):
                lf.secrets = []
                changed = True
            if amount is not None:
                desired = max(0, int(amount))
                try:
                    current = int(getattr(lf, 'amount', 0) or 0)
                except Exception:
                    current = -1
                if current != desired:
                    lf.amount = desired
                    changed = True
            if active is not None and bool(getattr(lf, 'active', False)) != bool(active):
                lf.active = bool(active)
                changed = True
            if changed:
                cardinal.account.save_lot(lf)
            return True
        except Exception as e:
            _log_event('funpay_lot_save_retry', level=logging.WARNING, lot_id=lot_id, attempt=attempt, error=str(e))
            if attempt < max(1, int(attempts)):
                time.sleep(min(0.3 * attempt, 1.0))
    return False
def _sync_lot_capacity(lot_id, binding, subscription, occupied):
    b = _normalize_binding(binding)
    cap = _capacity_for_binding(b, subscription, occupied)
    if not b['enabled'] or b['manual_disabled']:
        _auto_disabled.pop(str(lot_id), None)
        _set_funpay_lot_fields(lot_id, False, 0)
        return cap
    if cap.get('reason') == 'no_free_slots' and (not bool(cfg_get('auto_deactivate_on_slots'))):
        return cap
    qty = int(cap.get('sellable_qty', 0) or 0)
    active = qty > 0
    if active:
        _auto_disabled.pop(str(lot_id), None)
    else:
        _auto_disabled[str(lot_id)] = time.time()
    _set_funpay_lot_fields(lot_id, active, qty)
    return cap
def _capacity_check_once(subscription=None, accounts=None):
    if not bool(cfg_get('plugin_enabled')):
        return {}
    try:
        if subscription is None or accounts is None:
            snap = _api_snapshot()
            subscription = snap['subscription']
            accounts = snap['accounts']
    except Exception:
        return {}
    occupied = _occupied_account_count(accounts)
    results = {}
    with _state_lock:
        bindings = {k: _normalize_binding(v) for k, v in _bindings.items() if isinstance(v, dict)}
        before = set(_auto_disabled)
    for lot_id, binding in bindings.items():
        try:
            results[lot_id] = _sync_lot_capacity(lot_id, binding, subscription, occupied)
        except Exception as e:
            _log_event('lot_capacity_sync_error', level=logging.WARNING, lot_id=lot_id, error=str(e))
    if before != set(_auto_disabled):
        try:
            _atomic_json(AUTO_DISABLED_FILE, dict(_auto_disabled))
        except Exception:
            pass
    return results
def _order_capacity_check(binding, amount):
    try:
        snap = _api_snapshot(force=True)
        sub = snap['subscription']
        accounts = snap['accounts']
        slots = _capacity_slot_snapshot(sub, accounts)
        connected = slots['occupied']
        _log_event('capacity_slot_check', details=f"limit={slots['limit']} api_accounts={slots['api_accounts']} reserved={slots['reserved']} occupied={slots['occupied']} free={slots['free']}")
        cap = _capacity_for_binding(binding, sub, connected)
        safe = int(amount) <= int(cap.get('sellable_qty', 0) or 0)
        queued = False
        if safe and bool(cfg_get('queue_enabled')) and (int(slots['free']) <= 0):
            queued = True
            cap['reason'] = 'queued_no_free_slots'
        elif safe and bool(cfg_get('queue_enabled')) and _queued_services() and (len(_queued_services()) >= int(slots['free'])):
            queued = True
            cap['reason'] = 'queued_fifo'
        cap['queue'] = queued
        cap['slot_debug'] = slots
        return (safe, cap, sub, accounts)
    except Exception as e:
        return (False, {'sellable_qty': 0, 'reason': 'backend_error', 'error': _human_error(e)}, {}, [])
def _object_value(value, key):
    return value.get(key) if isinstance(value, dict) else getattr(value, key, None)
def _lot_id_text(value):
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    return text if text.isdigit() and int(text) > 0 else None
def _lot_id_candidates(value, depth=0, seen=None):
    if value is None or depth > 3:
        return []
    seen = set() if seen is None else seen
    marker = id(value)
    if marker in seen:
        return []
    seen.add(marker)
    result = []
    for key in ('lot_id', 'offer_id'):
        item = _lot_id_text(_object_value(value, key))
        if item:
            result.append(item)
    for key in ('lot', 'offer', 'node', 'fields', 'data'):
        child = _object_value(value, key)
        if child is None:
            continue
        scalar = _lot_id_text(child)
        if scalar and key in ('lot', 'offer'):
            result.append(scalar)
            continue
        child_id = _lot_id_text(_object_value(child, 'id'))
        if child_id and key in ('lot', 'offer'):
            result.append(child_id)
        result.extend(_lot_id_candidates(child, depth + 1, seen))
    return list(dict.fromkeys(result))
def _order_texts(value):
    result = []
    for attr in ('full_description', 'description', 'short_description', 'title'):
        raw = _object_value(value, attr)
        if raw:
            text = re.sub('\\s+', ' ', str(raw)).strip()
            if text and text not in result:
                result.append(text)
    return result
def _find_binding_for_order(order, event=None):
    with _state_lock:
        bindings = {str(k): _normalize_binding(v) for k, v in _bindings.items() if isinstance(v, dict)}
    if not bindings:
        return (None, None)
    oid = str(_object_value(order, 'id') or '')
    candidates = _lot_id_candidates(event) + _lot_id_candidates(order)
    texts = _order_texts(order)
    if oid and cardinal is not None and (getattr(cardinal, 'account', None) is not None):
        try:
            full = cardinal.account.get_order(oid)
            candidates.extend(_lot_id_candidates(full))
            texts.extend((x for x in _order_texts(full) if x not in texts))
        except Exception as e:
            _log_event('order_match_lookup_error', level=logging.WARNING, order_id=oid, error=str(e))
    for lot_id in dict.fromkeys(candidates):
        if lot_id in bindings:
            _log_event('order_lot_match', order_id=oid or '?', lot_id=lot_id, source='id')
            return (lot_id, bindings[lot_id])
    for text in texts:
        normalized = re.sub('\\s+', ' ', text).strip().casefold()
        matches = [lot_id for lot_id, b in bindings.items() if re.sub('\\s+', ' ', str(b.get('lot_name') or '')).strip().casefold() == normalized]
        if len(matches) == 1:
            _log_event('order_lot_match', order_id=oid or '?', lot_id=matches[0], source='exact_title')
            return (matches[0], bindings[matches[0]])
    _log_event('binding_miss', level=logging.WARNING, order_id=oid or '?')
    return (None, None)
def _order_buyer_name(order, event=None):
    for source in (order, event):
        if source is None:
            continue
        direct = _object_value(source, 'buyer_username')
        if direct:
            return str(direct).strip().lstrip('@')
        buyer = _object_value(source, 'buyer')
        if isinstance(buyer, str) and buyer.strip():
            return buyer.strip().lstrip('@')
        for key in ('username', 'name', 'login'):
            raw = _object_value(buyer, key)
            if raw:
                return str(raw).strip().lstrip('@')
    return ''
def _message_chat_id(msg):
    for raw in (_object_value(msg, 'chat_id'), _object_value(_object_value(msg, 'chat'), 'id')):
        try:
            if raw is not None:
                return int(raw)
        except Exception:
            pass
    return None
def _order_chat_id(order, event=None):
    for source in (order, event):
        if source is None:
            continue
        for raw in (_object_value(source, 'chat_id'), _object_value(_object_value(source, 'chat'), 'id')):
            try:
                if raw is not None:
                    return int(raw)
            except Exception:
                pass
        msg = _object_value(source, 'message')
        if msg is not None:
            cid = _message_chat_id(msg)
            if cid is not None:
                return cid
    return None
def _message_text(msg):
    return str(_object_value(msg, 'content') or _object_value(msg, 'text') or '').strip()
def _message_author_name(msg):
    for raw in (_object_value(msg, 'author_username'), _object_value(msg, 'username'), _object_value(_object_value(msg, 'author'), 'username'), _object_value(msg, 'author')):
        if raw is not None and (not isinstance(raw, (dict, list, tuple))):
            text = str(raw).strip().lstrip('@')
            if text:
                return text
    return ''
def _find_service_for_message(msg):
    chat_id = _message_chat_id(msg)
    if chat_id is None:
        return None
    author = _message_author_name(msg).casefold()
    exact = []
    unbound = []
    with _state_lock:
        for oid, service in _services.items():
            if not isinstance(service, dict) or str(service.get('step') or '') not in ('await_login', 'await_password', 'await_guard', 'await_games'):
                continue
            buyer = str(service.get('buyer') or '').strip().lstrip('@').casefold()
            saved = service.get('chat_id')
            if saved is not None:
                try:
                    if int(saved) != int(chat_id):
                        continue
                except Exception:
                    continue
                if author and buyer and (author != buyer):
                    continue
                exact.append((str(oid), service))
                continue
            if author and buyer and (author == buyer):
                unbound.append((str(oid), service))
        candidates = exact or unbound
        if not candidates:
            return None
        candidates.sort(key=lambda x: float(x[1].get('created_at', 0) or 0))
        oid, selected = candidates[0]
        if selected.get('chat_id') is None:
            selected['chat_id'] = int(chat_id)
            _services[oid]['chat_id'] = int(chat_id)
            _save_runtime_state()
        return dict(selected)
def _queued_services():
    with _state_lock:
        rows = [(str(k), dict(v)) for k, v in _services.items() if isinstance(v, dict) and str(v.get('step') or '') == 'queued']
    return sorted(rows, key=lambda x: float(x[1].get('created_at', 0) or 0))
def _queue_position(order_id):
    for index, (oid, _) in enumerate(_queued_services(), 1):
        if oid == str(order_id):
            return index
    return 0
def _service_progress(service, now_ts=None):
    now = float(now_ts if now_ts is not None else time.time())
    try:
        paid = max(0.0, float(service.get('duration_hours') or 0) * 3600.0)
    except Exception:
        paid = 0.0
    try:
        started = float(service.get('started_at') or 0)
    except Exception:
        started = 0.0
    try:
        ends = float(service.get('ends_at') or 0)
    except Exception:
        ends = 0.0
    elapsed = max(0.0, min(paid, now - started)) if started else 0.0
    remaining = max(0.0, ends - now) if ends else max(0.0, paid - elapsed)
    return (paid, elapsed, remaining)
def _service_time_fits(service, subscription):
    safe, reason = _safe_subscription_hours(subscription)
    try:
        duration = max(0.0, float(service.get('duration_hours') or 0))
    except Exception:
        duration = 0.0
    return (duration > 0 and safe + 1e-09 >= duration, safe, reason if reason else 'not_enough_time' if safe + 1e-09 < duration else '')
def _start_service_with_games(service, games):
    oid = str(service.get('order_id') or '')
    buyer = str(service.get('buyer') or '')
    chat_id = service.get('chat_id')
    selected = _normalize_appids(games, max(1, int(service.get('max_games') or 1)))
    if not selected:
        return False
    try:
        snap = _api_snapshot(force=True)
        sub = snap['subscription']
        ok, safe, reason = _service_time_fits(service, sub)
        if not ok:
            raise ValueError(_capacity_reason_text(reason))
        if len(selected) > max(0, int(sub.get('games', 0) or 0)):
            raise ValueError('Выбрано больше игр, чем разрешает тариф.')
        account_id = int(service.get('api_account_id') or 0)
        if account_id <= 0:
            raise ValueError('Steam-аккаунт ещё не подключён.')
        _get_client().patch_account(account_id, games=selected, running=True, mode='hours', hidden=bool(service.get('hidden', False)))
        _invalidate_snapshot()
    except Exception as e:
        human = _human_error(e)
        _fp_send(chat_id, _buyer_message('farm_start_failed', order_id=oid, reason=human), buyer)
        _notify_admin(f'⚠️ Заказ #{html.escape(oid)}: запуск — {html.escape(human)}', etype='error')
        return False
    started = time.time()
    ends = started + float(service.get('duration_hours') or 0) * 3600.0
    end_text = datetime.fromtimestamp(ends).strftime('%d.%m.%Y %H:%M')
    with _state_lock:
        current = _services.get(oid)
        if current:
            current.update({'games': selected, 'started_at': started, 'ends_at': ends, 'step': 'running', 'error': ''})
            current.pop('slot_reserved_at', None)
    _save_runtime_state()
    _fp_send(chat_id, _buyer_message('farm_started', order_id=oid, games=' '.join(map(str, selected)), hours=f"{float(service.get('duration_hours') or 0):g}", end_time=end_text), buyer)
    _notify_admin(f"🟢 <b>Фарм запущен #{html.escape(oid)}</b>\nSteam: <code>{html.escape(str(service.get('steam_login') or ''))}</code>\nДо: {end_text}", etype='started')
    try:
        _capacity_check_once()
    except Exception:
        pass
    return True
def _handle_service_message(service, text):
    oid = str(service.get('order_id') or '')
    buyer = str(service.get('buyer') or '')
    chat_id = service.get('chat_id')
    step = str(service.get('step') or '')
    clean = str(text or '').strip()
    if not clean:
        return True
    if step == 'await_login':
        if len(clean) > 128:
            _fp_send(chat_id, _buyer_message('login_invalid', order_id=oid), buyer)
            return True
        with _state_lock:
            current = _services.get(oid)
            if current:
                current['steam_login'] = clean
                current['step'] = 'await_password'
                current['slot_reserved_at'] = time.time()
        _save_runtime_state()
        _fp_send(chat_id, _buyer_message('ask_password', order_id=oid), buyer)
        return True
    if step == 'await_password':
        try:
            client = _get_client()
            if client is None:
                raise ValueError('API временно недоступен')
            result = client.login_account(str(service.get('steam_login') or ''), clean, [], bool(service.get('hidden', False)))
            _invalidate_snapshot()
        except Exception as e:
            _fp_send(chat_id, _buyer_message('login_failed', order_id=oid, reason=_human_error(e)), buyer)
            return True
        if str(result.get('need') or '') == 'guard_code' and result.get('session_id'):
            with _state_lock:
                current = _services.get(oid)
                if current:
                    current['step'] = 'await_guard'
                    current['session_id'] = str(result['session_id'])
                    current['slot_reserved_at'] = time.time()
            _save_runtime_state()
            _fp_send(chat_id, _buyer_message('ask_guard', order_id=oid), buyer)
            return True
        try:
            account_id = int(result.get('id') or 0)
        except Exception:
            account_id = 0
        if account_id <= 0:
            _fp_send(chat_id, _buyer_message('account_connect_failed', order_id=oid), buyer)
            return True
        with _state_lock:
            current = _services.get(oid)
            if current:
                current['api_account_id'] = account_id
                current['step'] = 'await_games'
                current.pop('slot_reserved_at', None)
        _save_runtime_state()
        current = dict(_services.get(oid) or service)
        if str(current.get('game_policy') or 'buyer') == 'fixed' and current.get('fixed_games'):
            return _start_service_with_games(current, current['fixed_games'])
        _fp_send(chat_id, _buyer_message('ask_games', order_id=oid, max_games=current.get('max_games', 1)), buyer)
        return True
    if step == 'await_guard':
        try:
            client = _get_client()
            if client is None:
                raise ValueError('API временно недоступен')
            result = client.submit_guard_code(str(service.get('session_id') or ''), clean)
            _invalidate_snapshot()
        except (FarmApiError, LocalFarmError) as e:
            if e.code == 'bad_code':
                _fp_send(chat_id, _buyer_message('guard_bad_code', order_id=oid), buyer)
                return True
            if e.code == 'login_expired':
                with _state_lock:
                    current = _services.get(oid)
                    if current:
                        current['step'] = 'await_password'
                        current['session_id'] = ''
                        current['slot_reserved_at'] = time.time()
                _save_runtime_state()
                _fp_send(chat_id, _buyer_message('guard_expired', order_id=oid), buyer)
                return True
            _fp_send(chat_id, _buyer_message('guard_failed', order_id=oid, reason=_human_error(e)), buyer)
            return True
        except Exception as e:
            _fp_send(chat_id, _buyer_message('guard_failed', order_id=oid, reason=_human_error(e)), buyer)
            return True
        try:
            account_id = int(result.get('id') or 0)
        except Exception:
            account_id = 0
        if account_id <= 0:
            _fp_send(chat_id, _buyer_message('account_connect_failed', order_id=oid), buyer)
            return True
        with _state_lock:
            current = _services.get(oid)
            if current:
                current['api_account_id'] = account_id
                current['step'] = 'await_games'
                current['session_id'] = ''
                current.pop('slot_reserved_at', None)
        _save_runtime_state()
        current = dict(_services.get(oid) or service)
        if str(current.get('game_policy') or 'buyer') == 'fixed' and current.get('fixed_games'):
            return _start_service_with_games(current, current['fixed_games'])
        _fp_send(chat_id, _buyer_message('ask_games', order_id=oid, max_games=current.get('max_games', 1)), buyer)
        return True
    if step == 'await_games':
        games = _normalize_appids(clean, max(1, int(service.get('max_games') or 1)))
        if not games:
            _fp_send(chat_id, _buyer_message('games_invalid', order_id=oid, max_games=int(service.get('max_games') or 1)), buyer)
            return True
        return _start_service_with_games(service, games)
    return False
def _should_auto_refund(reason):
    return str(reason or '') in {'no_subscription', 'bad_expiry', 'not_enough_time', 'games_over_plan'}
def _try_refund(order_id):
    try:
        if cardinal is None or getattr(cardinal, 'account', None) is None:
            return False
        cardinal.account.refund(str(order_id))
        _log_event('refund_success', order_id=order_id)
        return True
    except Exception as e:
        _log_event('refund_error', level=logging.WARNING, order_id=order_id, error=str(e))
        return False
def handle_new_order(cardinal_obj, event, *args):
    global cardinal
    if cardinal is None and cardinal_obj is not None:
        cardinal = cardinal_obj
    if not bool(cfg_get('plugin_enabled')):
        return
    order = getattr(event, 'order', None) or event
    oid = str(_object_value(order, 'id') or '').strip()
    if not oid:
        return
    with _state_lock:
        if oid in _services:
            return
    lot_id, binding = _find_binding_for_order(order, event)
    if not lot_id or not binding or (not bool(binding.get('enabled', True))):
        return
    try:
        quantity = max(1, int(_object_value(order, 'amount') or 1))
    except Exception:
        quantity = 1
    hours = _service_duration_hours(binding, quantity)
    buyer = _order_buyer_name(order, event)
    chat_id = _order_chat_id(order, event)
    safe, capacity, sub, accounts = _order_capacity_check(binding, quantity)
    queued = bool(capacity.get('queue')) if safe else False
    service = {'order_id': oid, 'lot_id': lot_id, 'lot_name': str(binding.get('lot_name') or ''), 'quantity': quantity, 'duration_hours': hours, 'max_games': int(binding.get('max_games') or 1), 'hidden': bool(binding.get('hidden', False)), 'game_policy': str(binding.get('game_policy') or 'buyer'), 'fixed_games': list(binding.get('fixed_games') or []), 'buyer': buyer, 'chat_id': chat_id, 'step': 'queued' if queued else 'await_login' if safe else 'blocked_capacity', 'steam_login': '', 'api_account_id': None, 'games': [], 'created_at': time.time(), 'queued_at': time.time() if queued else None, 'started_at': None, 'ends_at': None, 'completed_at': None, 'error': '' if safe else str(capacity.get('reason') or 'capacity'), 'backend': _backend_mode()}
    with _state_lock:
        if oid in _services:
            return
        _services[oid] = service
    _save_runtime_state()
    _log_event('farm_order_received', order_id=oid, lot_id=lot_id, quantity=quantity, hours=hours, buyer=buyer or 'unknown', queued=queued)
    if queued:
        pos = _queue_position(oid) or 1
        _fp_send(chat_id, _buyer_message('queued', order_id=oid, position=pos), buyer)
        _notify_admin(f'🕒 <b>Заказ #{html.escape(oid)} в очереди</b>\nВремя: {hours:g} ч. · позиция {pos}', etype='new_order')
        return
    if not safe:
        reason_code = str(capacity.get('reason') or '')
        reason = _capacity_reason_text(reason_code)
        if bool(cfg_get('auto_refund_enabled')) and _should_auto_refund(reason_code) and _try_refund(oid):
            with _state_lock:
                current = _services.get(oid)
                if current:
                    current.update({'step': 'refunded', 'refunded_at': time.time(), 'completed_at': time.time(), 'error': reason_code, 'refund_status': 'AUTO'})
            _save_runtime_state()
            _fp_send(chat_id, _buyer_message('auto_refund', order_id=oid, reason=reason), buyer)
            return
        _fp_send(chat_id, _buyer_message('blocked', order_id=oid, reason=reason), buyer)
        _notify_admin(f'⚠️ <b>Заказ #{html.escape(oid)} ожидает решения</b>\n{html.escape(reason)}', etype='capacity')
        return
    _fp_send(chat_id, _buyer_message('order_paid', order_id=oid, hours=f'{hours:g}', buyer=buyer), buyer)
    _notify_admin(f'🛒 <b>Новый заказ #{html.escape(oid)}</b>\nЛот: <code>{html.escape(lot_id)}</code>\nВремя: <b>{hours:g} ч.</b>', etype='new_order')
def _stop_service_now(order_id, final_step='stopped_manual', reason='manual'):
    oid = str(order_id or '').lstrip('#').strip()
    with _state_lock:
        service = dict(_services.get(oid) or {})
    if not service:
        return False
    try:
        account_id = int(service.get('api_account_id') or 0)
    except Exception:
        account_id = 0
    if account_id <= 0:
        now = time.time()
        with _state_lock:
            current = _services.get(oid)
            if not current:
                return False
            current.update({'step': str(final_step), 'completed_at': now, 'ends_at': now, 'api_account_id': None, 'error': ''})
            current.pop('slot_reserved_at', None)
            current.pop('session_id', None)
            current.pop('pending_final_step', None)
            current.pop('pending_reason', None)
        _save_runtime_state()
        try:
            _capacity_check_once()
        except Exception:
            pass
        return True
    client = _get_client()
    stop_ok = False
    delete_ok = False
    error = 'API недоступен' if client is None else ''
    if client is not None:
        for attempt in range(1, 4):
            try:
                client.patch_account(account_id, running=False)
                stop_ok = True
                break
            except Exception as e:
                error = _human_error(e)
                _log_event('service_stop_retry', level=logging.WARNING, order_id=oid, attempt=attempt, error=error)
                time.sleep(0.2 * attempt)
        try:
            client.delete_account(account_id)
            delete_ok = True
            _invalidate_snapshot()
        except Exception as e:
            error = error or _human_error(e)
    now = time.time()
    finalized = bool(delete_ok)
    with _state_lock:
        current = _services.get(oid)
        if not current:
            return False
        current['ends_at'] = now
        current.pop('slot_reserved_at', None)
        current.pop('session_id', None)
        if finalized:
            current.update({'step': str(final_step), 'completed_at': now, 'api_account_id': None, 'error': ''})
            current.pop('pending_final_step', None)
            current.pop('pending_reason', None)
        else:
            current.update({'step': 'stop_retry', 'pending_final_step': str(final_step), 'pending_reason': str(reason), 'error': f"{reason}_stop: {error or 'не подтверждено'}"})
    _save_runtime_state()
    if finalized:
        try:
            _capacity_check_once()
        except Exception:
            pass
    return finalized
def _stop_service_for_refund(order_id, status):
    oid = str(order_id or '').lstrip('#').strip()
    with _state_lock:
        exists = isinstance(_services.get(oid), dict)
    if not exists:
        return False
    finalized = _stop_service_now(oid, 'refunded', 'refund')
    now = time.time()
    with _state_lock:
        current = _services.get(oid)
        if current:
            current['refund_status'] = str(status).upper()
            current['refunded_at'] = now
            if finalized:
                current['step'] = 'refunded'
                current['completed_at'] = current.get('completed_at') or now
            else:
                current['pending_final_step'] = 'refunded'
                current['pending_reason'] = 'refund'
            current.pop('slot_reserved_at', None)
            buyer = str(current.get('buyer') or '')
            chat_id = current.get('chat_id')
        else:
            buyer = ''
            chat_id = None
    _save_runtime_state()
    _log_event('funpay_refund_stop', order_id=oid, status=str(status).upper(), finalized=finalized)
    if finalized:
        _fp_send(chat_id, _buyer_message('refunded', order_id=oid), buyer)
    _notify_admin(f'↩️ <b>Возврат по заказу #{html.escape(oid)}</b>\n' + ('Фарм остановлен.' if finalized else 'Остановка не подтверждена API, включены повторные попытки.'), etype='completed' if finalized else 'error')
    return True
def _normalize_order_status(event):
    order = getattr(event, 'order', None)
    for value in (getattr(event, 'new_status', None), getattr(event, 'status', None), _object_value(order, 'status') if order is not None else None):
        if value is None:
            continue
        text = str(getattr(value, 'name', value)).strip().upper()
        if '.' in text:
            text = text.rsplit('.', 1)[-1]
        if text:
            return text
    return ''
def _event_order_id(event):
    order = getattr(event, 'order', None)
    for value in (_object_value(order, 'id') if order is not None else None, getattr(event, 'order_id', None), _object_value(event, 'id')):
        if value:
            return str(value).lstrip('#').strip()
    return ''
def handle_order_status_changed(cardinal_obj, event, *args):
    global cardinal
    if cardinal is None and cardinal_obj is not None:
        cardinal = cardinal_obj
    status = _normalize_order_status(event)
    if status not in {'REFUNDED', 'PARTIALLY_REFUNDED'}:
        return
    oid = _event_order_id(event)
    if oid:
        _stop_service_for_refund(oid, status)
ORDER_PAID_RE = re.compile('оплатил(?:а)?\\s+(?:заказ|товар)\\s*#?([A-Za-z0-9]+)', re.I)
ORDER_REFUND_RE = re.compile('(?:возврат|частичн\\w* возврат).*?#([A-Za-z0-9]+)', re.I)
def handle_new_message(cardinal_obj, event, *args):
    global cardinal
    if cardinal is None and cardinal_obj is not None:
        cardinal = cardinal_obj
    msg = getattr(event, 'message', None) or event
    text = _message_text(msg)
    if not text:
        return
    message_type = str(getattr(_object_value(msg, 'type'), 'name', _object_value(msg, 'type') or '')).upper()
    if message_type in {'REFUND', 'PARTIAL_REFUND', 'REFUND_BY_ADMIN'}:
        match = ORDER_REFUND_RE.search(text)
        oid = match.group(1) if match else ''
        if not oid:
            cid = _message_chat_id(msg)
            with _state_lock:
                candidates = [str(k) for k, v in _services.items() if isinstance(v, dict) and v.get('chat_id') is not None and (str(v.get('step') or '') not in {'completed', 'stopped_manual', 'refunded'}) and (int(v.get('chat_id')) == int(cid or -1))]
            oid = candidates[0] if len(candidates) == 1 else ''
        if oid:
            _stop_service_for_refund(oid, 'PARTIALLY_REFUNDED' if message_type == 'PARTIAL_REFUND' else 'REFUNDED')
        return
    service = _find_service_for_message(msg)
    if service is not None:
        _handle_service_message(service, text)
        return
    paid = ORDER_PAID_RE.search(text)
    if not paid or cardinal is None or getattr(cardinal, 'account', None) is None:
        return
    oid = paid.group(1)
    with _state_lock:
        if oid in _services:
            return
    try:
        full = cardinal.account.get_order(oid)
    except Exception:
        return
    if 'PAID' not in str(_object_value(full, 'status') or '').upper():
        return
    handle_new_order(cardinal, SimpleNamespace(order=full, lot_id=_object_value(full, 'lot_id'), offer_id=_object_value(full, 'offer_id')))
def _promote_queue(subscription=None, accounts=None):
    if not bool(cfg_get('queue_enabled')):
        return 0
    try:
        if subscription is None or accounts is None:
            snap = _api_snapshot(force=True)
            subscription = snap['subscription']
            accounts = snap['accounts']
        slots = _capacity_slot_snapshot(subscription, accounts)
        free = slots['free']
    except Exception:
        return 0
    if free <= 0:
        return 0
    promoted = 0
    occupied = int(slots['occupied'])
    for oid, service in _queued_services():
        if promoted >= free:
            break
        with _state_lock:
            raw = _bindings.get(str(service.get('lot_id') or ''))
        if not isinstance(raw, dict):
            continue
        binding = _normalize_binding(raw)
        cap = _capacity_for_binding(binding, subscription, occupied + promoted)
        try:
            quantity = max(1, int(service.get('quantity') or 1))
        except Exception:
            quantity = 1
        if quantity > int(cap.get('sellable_qty', 0) or 0):
            continue
        with _state_lock:
            current = _services.get(oid)
            if not current or current.get('step') != 'queued':
                continue
            current.update({'step': 'await_login', 'queue_started_at': time.time(), 'error': ''})
        promoted += 1
        _fp_send(service.get('chat_id'), _buyer_message('slot_available', order_id=oid), str(service.get('buyer') or ''))
    if promoted:
        _save_runtime_state()
    return promoted
def _service_check_once(now_ts=None, client=None):
    now = float(now_ts if now_ts is not None else time.time())
    api = client or _get_client()
    if api is None:
        return False
    changed = False
    with _state_lock:
        rows = [(str(k), dict(v)) for k, v in _services.items() if isinstance(v, dict)]
    for oid, service in rows:
        step = str(service.get('step') or '')
        if step not in {'running', 'stop_retry'}:
            continue
        try:
            ends = float(service.get('ends_at') or 0)
        except Exception:
            ends = 0
        if step == 'running' and (ends <= 0 or now < ends):
            continue
        target = 'completed' if step == 'running' else str(service.get('pending_final_step') or 'completed')
        try:
            account_id = int(service.get('api_account_id') or 0)
        except Exception:
            account_id = 0
        try:
            if account_id > 0:
                api.patch_account(account_id, running=False)
                api.delete_account(account_id)
                _invalidate_snapshot()
        except Exception as e:
            with _state_lock:
                current = _services.get(oid)
                if current:
                    current['step'] = 'stop_retry'
                    current['pending_final_step'] = target
                    current['error'] = 'stop_failed: ' + _human_error(e)
            changed = True
            continue
        with _state_lock:
            current = _services.get(oid)
            if current:
                current.update({'step': target, 'completed_at': now, 'api_account_id': None, 'error': ''})
                current.pop('pending_final_step', None)
                current.pop('pending_reason', None)
        changed = True
        buyer = str(service.get('buyer') or '')
        chat_id = service.get('chat_id')
        if target == 'completed':
            _fp_send(chat_id, _buyer_message('farm_completed', order_id=oid), buyer)
            _notify_admin(f'✅ <b>Фарм завершён #{html.escape(oid)}</b>', etype='completed')
        elif target == 'refunded':
            _fp_send(chat_id, _buyer_message('refunded', order_id=oid), buyer)
            _notify_admin(f'↩️ <b>Фарм остановлен после возврата #{html.escape(oid)}</b>', etype='completed')
        elif target == 'stopped_manual':
            _fp_send(chat_id, _buyer_message('stopped_manual', order_id=oid), buyer)
    if changed:
        _save_runtime_state()
    return changed
def _subscription_notifications(subscription, accounts, now_ts=None):
    now = float(now_ts if now_ts is not None else time.time())
    sub = dict(subscription or {})
    expires = None if str(sub.get('backend') or '').lower() == 'local' else _parse_api_datetime(sub.get('expires_at'))
    changed = False
    if bool(cfg_get('notify_near_expiry')) and bool(sub.get('active')) and expires:
        hours = max(0.0, (expires - now) / 3600.0)
        for threshold in (24, 6):
            marker = f'expiry:{int(expires)}:{threshold}'
            if hours <= threshold and (not _notify_state.get(marker)):
                _notify_state[marker] = now
                _notify_admin(f'⚠️ До окончания подписки меньше {threshold} ч. Осталось около {hours:.1f} ч.', etype='subscription')
                changed = True
    reconnect = set()
    for account in accounts or []:
        if not isinstance(account, dict) or not account.get('needs_reconnect'):
            continue
        try:
            aid = int(account.get('id') or 0)
        except Exception:
            aid = 0
        if aid <= 0:
            continue
        reconnect.add(aid)
        marker = f'reconnect:{aid}'
        if not _notify_state.get(marker):
            _notify_state[marker] = now
            _notify_admin(f"⚠️ Steam-аккаунт <code>{html.escape(str(account.get('login') or aid))}</code> требует переподключения.", etype='reconnect')
            changed = True
    for key in list(_notify_state):
        if str(key).startswith('reconnect:'):
            try:
                aid = int(str(key).split(':', 1)[1])
            except Exception:
                continue
            if aid not in reconnect:
                _notify_state.pop(key, None)
                changed = True
    if changed:
        _save_runtime_state()
def _background_loop():
    while not _stop_event.is_set():
        try:
            snap = _api_snapshot(force=True)
            client = _get_client()
            changed = _service_check_once(client=client)
            if changed:
                snap = _api_snapshot(force=True)
            _promote_queue(snap['subscription'], snap['accounts'])
            _subscription_notifications(snap['subscription'], snap['accounts'])
            _capacity_check_once(snap['subscription'], snap['accounts'])
        except Exception as e:
            _log_event('background_error', level=logging.WARNING, error=str(e))
        try:
            wait = max(30.0, min(3600.0, float(cfg_get('capacity_check_sec') or 60)))
        except Exception:
            wait = 60.0
        if _stop_event.wait(wait):
            break
def _toggle_label(key):
    return '🟢 ВКЛ' if bool(cfg_get(key)) else '🔴 ВЫКЛ'
def _service_step_text(step):
    return {'queued': '🕒 в очереди', 'await_login': 'ожидается логин', 'await_password': 'ожидается пароль', 'await_guard': 'ожидается Steam Guard', 'await_games': 'ожидаются игры', 'running': '🟢 фарм идёт', 'stop_retry': '⚠️ повтор остановки', 'blocked_capacity': '🔴 заблокирован лимитом', 'completed': '✅ завершён', 'stopped_manual': '⏹ остановлен вручную', 'disconnected': '🗑 аккаунт отключён', 'refunded': '↩️ возврат'}.get(str(step or ''), str(step or 'неизвестно'))
def _plugin_home(chat_id, message_id=None):
    text = f'🧩 <b>{NAME}</b>\n📦 Версия: <code>{VERSION}</code>\n👥 Авторы: <a href="{SERVICE_AUTHOR_URL}">@dmitry_mak09</a>, <a href="{CREATOR_URL}">@tinechelovec</a>'
    kb = _make_kb([[('⚙️ Настройки', 'sfp_main'), ('ℹ️ Информация', 'sfp_info')], [('⬆️ Обновить', 'sfp_update'), ('🗑 Удалить', 'sfp_delete_ask')], [('🔙 К списку плагинов', CB_PLUGINS_LIST_OPEN)]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_main(chat_id, message_id=None):
    key = str(cfg_get('api_key') or '')
    with _state_lock:
        lots = len(_bindings)
        active = sum((1 for v in _services.values() if isinstance(v, dict) and str(v.get('step') or '') not in FINAL_SERVICE_STEPS))
    mode = _backend_mode()
    engine_state = '🟢 готов' if (key if mode == 'api' else _local_dependency_ready()) else '🟠 требует настройки'
    text = f"⚙️ <b>Панель Steam Farm</b>\n\n• Состояние: <b>{('🟢 включён' if cfg_get('plugin_enabled') else '🔴 выключен')}</b>\n• Движок: <b>{_backend_label(mode)}</b>\n• Движок готов: <b>{engine_state}</b>\n• Лотов: <b>{lots}</b>\n• Активных заказов: <b>{active}</b>"
    kb = _make_kb([[('🚜 Движок фарма', 'sfp_backend')], [('⚙️ Настройки плагина', 'sfp_plugin_settings')], [('🎟 Настройка лотов', 'sfp_lots')], [('📊 Статистика', 'sfp_stats')], [('◀️ Меню плагина', 'sfp_home')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_backend(chat_id, message_id=None):
    mode = _backend_mode()
    active = _active_service_count()
    lines = ['🚜 <b>Движок фарма</b>', '', f'Сейчас: <b>{_backend_label(mode)}</b>', f'Активных заказов: <b>{active}</b>', '', 'API — платный внешний сервис.\nLocal — бесплатный фарм на вашем сервере.']
    if active:
        lines.append('\n⚠️ Переключение заблокировано до завершения активных заказов.')
    rows = [
        [(('✅ ' if mode == 'api' else '') + '☁️ API', 'sfp_backend_api'), (('✅ ' if mode == 'local' else '') + '🖥 Local', 'sfp_backend_local')],
        [('☁️ Настройки API', 'sfp_api'), ('🖥 Настройки Local', 'sfp_local')],
        [('◀️ Назад', 'sfp_main')],
    ]
    _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb(rows)) if message_id else _tg_send(chat_id, '\n'.join(lines), _make_kb(rows))
def _menu_api(chat_id, message_id=None, live=True):
    key = str(cfg_get('api_key') or '')
    balance = None
    sub = None
    error = ''
    client = _get_api_client()
    if client and live:
        try:
            sub = client.get_subscription()
            balance = client.get_balance_kop()
        except Exception as e:
            error = _human_error(e)
    lines = ['☁️ <b>Dim4n4ik API</b>', '', f"Используется: <b>{'✅ да' if _backend_mode() == 'api' else 'нет'}</b>", f'🔑 API-ключ: <code>{html.escape(_mask_key(key))}</code>']
    if balance is not None:
        lines.append(f'💰 Баланс: <b>{_fmt_rub(balance)}</b>')
    if isinstance(sub, dict):
        lines.append(f"💳 Подписка: <b>{(html.escape(str(sub.get('plan_name') or sub.get('plan') or 'активна')) if sub.get('active') else 'нет')}</b>")
    if error:
        lines.append(f'\n⚠️ {html.escape(error)}')
    rows = []
    if key:
        rows.extend([[('🔄 Сменить ключ', 'sfp_setkey'), ('🗑 Удалить ключ', 'sfp_keydel_ask')], [('🩺 Проверить API', 'sfp_api_health'), ('💳 Подписка', 'sfp_subscription')]])
    else:
        rows.extend([[('🔑 Добавить API-ключ', 'sfp_setkey')], [('💳 Подписка', 'sfp_subscription')]])
    if _backend_mode() != 'api':
        rows.append([('✅ Использовать API', 'sfp_backend_api')])
    rows.append([('◀️ К движкам', 'sfp_backend')])
    text = '\n'.join(lines)
    _tg_edit(chat_id, message_id, text, _make_kb(rows)) if message_id else _tg_send(chat_id, text, _make_kb(rows))
def _menu_local(chat_id, message_id=None, live=True):
    status = _local_runtime_status(live=live)
    health = status.get('health') or {}
    accounts = status.get('accounts') or []
    installed = bool(status.get('installed'))
    daemon_ok = bool(health.get('ok'))
    lines = [
        '🖥 <b>Local backend</b>', '',
        f"Используется: <b>{'✅ да' if _backend_mode() == 'local' else 'нет'}</b>",
        f"Node.js: <b>{'✅ готов' if status.get('node') else '⚪️ установится автоматически'}</b>",
        f"steam-user: <b>{'✅ установлен' if installed else '❌ не установлен'}</b>",
        f"Helper: <b>{'🟢 работает' if daemon_ok else ('🟠 не запущен' if installed else '⚪️ не готов')}</b>",
        f"Аккаунты: <b>{len(accounts)} / {int(cfg_get('local_max_accounts') or 3)}</b>",
        f"Игры на аккаунт: <b>до {int(cfg_get('local_max_games') or 32)}</b>",
    ]
    if status.get('error'):
        lines.append(f"\n⚠️ {html.escape(str(status.get('error')))}")
    rows = [
        [('📦 Установить / обновить', 'sfp_local_install'), ('🩺 Проверить', 'sfp_local_health')],
        [('👥 Лимит аккаунтов', 'sfp_local_accounts'), ('🎮 Лимит игр', 'sfp_local_games')],
        [('🔄 Перезапустить helper', 'sfp_local_restart')],
        [('◀️ Назад', 'sfp_backend')],
    ]
    text = '\n'.join(lines)
    _tg_edit(chat_id, message_id, text, _make_kb(rows)) if message_id else _tg_send(chat_id, text, _make_kb(rows))
def _local_install_result_keyboard():
    return [[('🔁 Повторить', 'sfp_local_install'), ('◀️ Назад', 'sfp_local')]]
def _local_install_worker(chat_id, message_id=None):
    try:
        result = _install_local_runtime()
        _local_console('Запускаю helper после установки...')
        pong = _start_local_daemon(force=True)
        version = str(pong.get('version') or result.get('version') or 'OK')
        _tg_edit(
            chat_id, message_id,
            f"✅ <b>Local backend установлен и запущен.</b>\n\nsteam-user: <code>{html.escape(version)}</code>\nПодробный вывод установки был показан в терминале Cardinal.",
            _make_kb(_local_install_result_keyboard()),
        )
    except Exception as e:
        _local_console(f'ОШИБКА установки Local backend: {_human_error(e)}')
        _tg_edit(
            chat_id, message_id,
            f"❌ <b>Не удалось установить Local backend.</b>\n\n{html.escape(_human_error(e))}\n\nПодробности смотрите в терминале Cardinal.",
            _make_kb(_local_install_result_keyboard()),
        )
def _menu_subscription(chat_id, message_id=None):
    client = _get_api_client()
    if not client:
        _tg_edit(chat_id, message_id, '🔑 Для подписки нужен API-ключ.', _make_kb([[('🏪 Аккаунт / API', 'sfp_api')]]))
        return
    try:
        sub = client.get_subscription()
    except Exception as e:
        _tg_edit(chat_id, message_id, f'❌ Подписка недоступна: {html.escape(_human_error(e))}', _make_kb([[('◀️ Назад', 'sfp_api')]]))
        return
    lines = ['💳 <b>Подписка</b>', '']
    if sub.get('active'):
        lines.extend([f"Тариф: <b>{html.escape(str(sub.get('plan_name') or sub.get('plan') or '—'))}</b>", f"👤 Аккаунтов: <b>{int(sub.get('accounts', 0) or 0)}</b>", f"🎮 Игр на аккаунт: <b>{int(sub.get('games', 0) or 0)}</b>", f"📅 До: <code>{html.escape(str(sub.get('expires_at') or '—'))}</code>"])
    else:
        lines.append('Активной подписки нет.')
    kb = _make_kb([[('🛒 Тарифы / продлить', 'sfp_plans')], [('◀️ Назад', 'sfp_api')]])
    _tg_edit(chat_id, message_id, '\n'.join(lines), kb) if message_id else _tg_send(chat_id, '\n'.join(lines), kb)
def _plan_by_code(code):
    try:
        client = _get_api_client()
        return next((p for p in client.get_plans() if str(p.get('code') or '') == str(code)), None) if client else None
    except Exception:
        return None
def _menu_plans(chat_id, message_id=None):
    client = _get_api_client()
    if not client:
        _menu_subscription(chat_id, message_id)
        return
    try:
        plans = client.get_plans()
    except Exception as e:
        _tg_edit(chat_id, message_id, f'❌ Тарифы недоступны: {html.escape(_human_error(e))}', _make_kb([[('◀️ Назад', 'sfp_subscription')]]))
        return
    rows = []
    lines = ['🛒 <b>Тарифы фарма часов</b>', '']
    for plan in plans:
        code = str(plan.get('code') or '')
        if not code or len(code) > 24 or code == 'custom':
            continue
        name = str(plan.get('name') or code)
        price = _fmt_rub(plan.get('price_kop', 0))
        accounts = plan.get('accounts')
        games = plan.get('games')
        suffix = f' · {accounts} акк. · {games} игр' if accounts is not None and games is not None else ''
        rows.append([(f'⏱ {name} · {price}{suffix}'[:60], f'sfp_plan:{code}')])
    rows.append([('◀️ Назад', 'sfp_subscription')])
    _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb(rows)) if message_id else _tg_send(chat_id, '\n'.join(lines), _make_kb(rows))
def _discounted_price(price, months):
    return int(round(max(0, int(price or 0)) * int(months) * (100 - PERIOD_DISCOUNTS.get(int(months), 0)) / 100.0))
def _menu_plan_periods(chat_id, message_id, plan):
    code = str(plan.get('code') or '')
    name = html.escape(str(plan.get('name') or code))
    price = int(plan.get('price_kop', 0) or 0)
    rows = []
    for a, b in ((1, 3), (6, 12)):
        def label(m):
            d = PERIOD_DISCOUNTS[m]
            return f'{m} мес. · {_fmt_rub(_discounted_price(price, m))}' + (f' · −{d}%' if d else '')
        rows.append([(label(a), f'sfp_plan_period:{code}:{a}'), (label(b), f'sfp_plan_period:{code}:{b}')])
    rows.append([('◀️ К тарифам', 'sfp_plans')])
    _tg_edit(chat_id, message_id, f'📅 <b>{name}</b>\n\nВыберите срок подписки.', _make_kb(rows))
def _prepare_purchase(chat_id, plan, months, message_id=None):
    code = str(plan.get('code') or '')
    nonce = uuid.uuid4().hex[:12]
    idem = f'farm-sub-{nonce}-{int(time.time())}'
    _purchase_confirm[int(chat_id)] = {'nonce': nonce, 'plan': code, 'months': int(months), 'accounts': 0, 'idem_key': idem, 'created_at': time.time()}
    cost = _discounted_price(int(plan.get('price_kop', 0) or 0), months)
    text = f"⚠️ <b>Подтверждение покупки</b>\n\nТариф: <b>{html.escape(str(plan.get('name') or code))}</b>\nСрок: <b>{months} мес.</b>\nОриентировочная стоимость: <b>{_fmt_rub(cost)}</b>\n\nФинальную стоимость подтвердит API."
    kb = _make_kb([[('✅ Купить / продлить', f'sfp_subbuy:{nonce}'), ('❌ Отмена', 'sfp_subscription')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_plugin_settings(chat_id, message_id=None):
    text = f"⚙️ <b>Настройки плагина</b>\n\n• Плагин: <b>{_toggle_label('plugin_enabled')}</b>\n• Автовозврат: <b>{_toggle_label('auto_refund_enabled')}</b>\n• Уведомления: <b>{_toggle_label('notifications_enabled')}</b>"
    kb = _make_kb([[('🧩 Состояние плагина', 'sfp_plugin_state')], [('📦 Заказы', 'sfp_orders')], [('🔔 Уведомления', 'sfp_notifications')], [('🛡 Безопасность', 'sfp_safety')], [('🧰 Обслуживание', 'sfp_maintenance')], [('◀️ Назад', 'sfp_main')]])
    if message_id:
        _tg_edit(chat_id, message_id, text, kb)
    else:
        _tg_send(chat_id, text, kb)
def _menu_plugin_state(chat_id, message_id=None):
    enabled = bool(cfg_get('plugin_enabled'))
    text = f"🧩 <b>Состояние плагина</b>\n\nСейчас: <b>{('🟢 Включён' if enabled else '🔴 Выключен')}</b>\n\nПри выключении новые заказы не принимаются. Уже запущенные продолжают контролироваться."
    kb = _make_kb([[(f"🧩 Плагин: {('ВКЛ' if enabled else 'ВЫКЛ')}", 'sfp_toggle_plugin')], [('◀️ Назад', 'sfp_plugin_settings')]])
    _tg_edit(chat_id, message_id, text, kb)
def _menu_orders(chat_id, message_id=None):
    with _state_lock:
        active = sum((1 for value in _services.values() if isinstance(value, dict) and str(value.get('step') or '') not in FINAL_SERVICE_STEPS))
        history = sum((1 for value in _services.values() if isinstance(value, dict) and str(value.get('step') or '') in FINAL_SERVICE_STEPS))
    text = f"📦 <b>Заказы</b>\n\n🚀 Активных: <b>{active}</b>\n🕘 В истории: <b>{history}</b>\n↩️ Автовозврат: <b>{_toggle_label('auto_refund_enabled')}</b>\n🎟 Автодеактивация при занятом лимите: <b>{_toggle_label('auto_deactivate_on_slots')}</b>\n"
    kb = _make_kb([[('🚀 Активные заказы', 'sfp_services')], [('🕘 История заказов', 'sfp_order_history')], [('💬 Сообщения', 'sfp_messages')], [(f"↩️ Автовозврат: {_toggle_label('auto_refund_enabled')}", 'sfp_toggle_refund')], [(f"🎟 Автодеактивация: {_toggle_label('auto_deactivate_on_slots')}", 'sfp_toggle_slot_deactivate')], [('◀️ Назад', 'sfp_plugin_settings')]])
    if message_id:
        _tg_edit(chat_id, message_id, text, kb)
    else:
        _tg_send(chat_id, text, kb)
def _menu_services(chat_id, message_id=None):
    with _state_lock:
        rows_data = [(str(k), dict(v)) for k, v in _services.items() if isinstance(v, dict) and str(v.get('step') or '') not in FINAL_SERVICE_STEPS]
    lines = ['🚀 <b>Активные заказы</b>']
    rows = []
    if not rows_data:
        lines.append('\nАктивных заказов сейчас нет.')
    for oid, s in sorted(rows_data, key=lambda x: float(x[1].get('created_at', 0) or 0)):
        step = _service_step_text(s.get('step'))
        login = str(s.get('steam_login') or '—')
        games = ' '.join(map(str, s.get('games') or s.get('fixed_games') or [])) or '—'
        lines.append(f"\n#{html.escape(oid)} · {html.escape(step)}\n@{html.escape(str(s.get('buyer') or '?'))} · Steam <code>{html.escape(login)}</code> · игры <code>{html.escape(games)}</code>")
        rows.append([(f'#{oid} · {step[:22]}', f'sfp_service:{oid}')])
    rows.append([('◀️ Назад', 'sfp_orders')])
    _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb(rows)) if message_id else _tg_send(chat_id, '\n'.join(lines), _make_kb(rows))
def _menu_order_history(chat_id, message_id=None):
    with _state_lock:
        data = [(str(k), dict(v)) for k, v in _services.items() if isinstance(v, dict) and str(v.get('step') or '') in FINAL_SERVICE_STEPS]
    data.sort(key=lambda x: float(x[1].get('completed_at') or x[1].get('created_at') or 0), reverse=True)
    lines = ['🕘 <b>История заказов</b>']
    rows = []
    if not data:
        lines.append('\nЗавершённых заказов пока нет.')
    for oid, s in data[:50]:
        step = _service_step_text(s.get('step'))
        lines.append(f"\n#{html.escape(oid)} · {html.escape(step)} · @{html.escape(str(s.get('buyer') or '?'))}")
        rows.append([(f'#{oid} · {step[:24]}', f'sfp_history:{oid}')])
    rows.append([('◀️ Назад', 'sfp_orders')])
    _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb(rows)) if message_id else _tg_send(chat_id, '\n'.join(lines), _make_kb(rows))
def _menu_service_detail(chat_id, message_id, order_id, back='sfp_services'):
    with _state_lock:
        s = dict(_services.get(str(order_id)) or {})
    if not s:
        _menu_services(chat_id, message_id)
        return
    paid, elapsed, remaining = _service_progress(s)
    games = ' '.join(map(str, s.get('games') or s.get('fixed_games') or [])) or '—'
    started = datetime.fromtimestamp(float(s['started_at'])).strftime('%d.%m.%Y %H:%M') if s.get('started_at') else '—'
    ends = datetime.fromtimestamp(float(s['ends_at'])).strftime('%d.%m.%Y %H:%M') if s.get('ends_at') else '—'
    text = f"🚀 <b>Заказ #{html.escape(str(order_id))}</b>\n\nСтатус: <b>{html.escape(_service_step_text(s.get('step')))}</b>\nПокупатель: <b>@{html.escape(str(s.get('buyer') or '?'))}</b>\nSteam: <code>{html.escape(str(s.get('steam_login') or '—'))}</code>\nИгры: <code>{html.escape(games)}</code>\n\nОплачено: <b>{_format_duration(paid)}</b>\nПрошло: <b>{_format_duration(elapsed)}</b>\nОсталось: <b>{_format_duration(remaining)}</b>\nСтарт: <b>{started}</b>\nКонец: <b>{ends}</b>"
    if s.get('refund_status'):
        text += f"\nВозврат: <b>{html.escape(str(s.get('refund_status')))}</b>"
    if s.get('error'):
        text += f"\n\n⚠️ {html.escape(str(s.get('error'))[:250])}"
    rows = []
    if str(s.get('step') or '') in {'running', 'stop_retry'}:
        rows.append([('⏹ Остановить досрочно', f'sfp_service_stop:{order_id}')])
    if s.get('api_account_id') and str(s.get('step') or '') not in FINAL_SERVICE_STEPS:
        rows.append([('🗑 Отключить Steam-аккаунт', f'sfp_service_disconnect:{order_id}')])
    rows.append([('◀️ Назад', back)])
    _tg_edit(chat_id, message_id, text, _make_kb(rows))
def _menu_notifications(chat_id, message_id=None):
    keys = [('notifications_enabled', '🔔 Все'), ('notify_new_order', '🛒 Новый заказ'), ('notify_started', '🚀 Фарм запущен'), ('notify_completed', '✅ Фарм завершён'), ('notify_errors', '⚠️ Ошибки'), ('notify_subscription', '💳 Подписка'), ('notify_capacity', '🎟 Лимиты / лоты'), ('notify_reconnect', '🔄 Reconnect')]
    rows = [[(f'{label}: {_toggle_label(key)}', f'sfp_ntgl:{key}')] for key, label in keys] + [[('◀️ Назад', 'sfp_plugin_settings')]]
    _tg_edit(chat_id, message_id, '🔔 <b>Уведомления</b>\n\nВыберите, какие события получать продавцу.', _make_kb(rows))
def _menu_messages(chat_id, message_id=None):
    configured = cfg_get('messages')
    rows = []
    lines = ['💬 <b>Сообщения покупателю</b>', '', 'Здесь можно изменить тексты, которые плагин отправляет покупателю.']
    for key, label in MESSAGE_LABELS.items():
        custom = isinstance(configured, dict) and str(configured.get(key) or '') != str(DEFAULT_MESSAGES.get(key) or '')
        mark = '✏️' if custom else '💬'
        rows.append([(f'{mark} {label}', f'sfp_msg:{key}')])
    rows.append([('♻️ Сбросить все тексты', 'sfp_messages_reset_ask')])
    rows.append([('◀️ Назад', 'sfp_orders')])
    kb = _make_kb(rows)
    text = '\n'.join(lines)
    if message_id:
        _tg_edit(chat_id, message_id, text, kb)
    else:
        _tg_send(chat_id, text, kb)
def _menu_message_detail(chat_id, message_id, key):
    if key not in DEFAULT_MESSAGES:
        _menu_messages(chat_id, message_id)
        return
    current = (cfg_get('messages') or {}).get(key, DEFAULT_MESSAGES[key])
    text = f"{html.escape(MESSAGE_LABELS.get(key, key))}\n\n<b>Текущий текст:</b>\n<code>{html.escape(str(current))}</code>\n\nДоступные переменные: <code>{html.escape(', '.join(('{' + x + '}' for x in sorted(MESSAGE_FIELDS))))}</code>"
    kb = _make_kb([[('✏️ Изменить', f'sfp_msg_edit:{key}')], [('♻️ Сбросить', 'sfp_msg_reset:' + key)], [('◀️ Назад', 'sfp_messages')]])
    _tg_edit(chat_id, message_id, text, kb)
def _menu_safety(chat_id, message_id=None):
    text = f"🛡 <b>Безопасность</b>\n\n🛡 Запас подписки: <b>{float(cfg_get('safety_buffer_hours') or 1):g} ч.</b>\n⏱ Проверка состояния: <b>{int(float(cfg_get('capacity_check_sec') or 60))} сек.</b>\n🕒 Очередь заказов: <b>{_toggle_label('queue_enabled')}</b>\n⚠️ Предупреждать об окончании: <b>{_toggle_label('notify_near_expiry')}</b>"
    kb = _make_kb([[('🛡 Запас подписки', 'sfp_set_buffer'), ('⏱ Интервал проверки', 'sfp_set_interval')], [(f"🕒 Очередь: {_toggle_label('queue_enabled')}", 'sfp_toggle_queue')], [(f"⚠️ Окончание тарифа: {_toggle_label('notify_near_expiry')}", 'sfp_toggle_expiry')], [('◀️ Назад', 'sfp_plugin_settings')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _service_stats_snapshot():
    try:
        reset = float(cfg_get('stats_reset_at') or 0)
    except Exception:
        reset = 0
    with _state_lock:
        rows = [dict(v) for v in _services.values() if isinstance(v, dict) and float(v.get('created_at', 0) or 0) >= reset]
    out = {'total': len(rows), 'active': 0, 'completed': 0, 'refunded': 0, 'units': 0, 'hours': 0.0, 'lots': {}}
    for s in rows:
        step = str(s.get('step') or '')
        refunded = step == 'refunded'
        out['active'] += step not in FINAL_SERVICE_STEPS
        out['completed'] += step == 'completed'
        out['refunded'] += refunded
        try:
            qty = max(1, int(s.get('quantity') or 1))
            hours = max(0.0, float(s.get('duration_hours') or 0))
        except Exception:
            qty = 1
            hours = 0
        if not refunded:
            out['units'] += qty
            out['hours'] += hours
        lot = out['lots'].setdefault(str(s.get('lot_id') or '—'), {'orders': 0, 'hours': 0.0})
        lot['orders'] += 1
        lot['hours'] += 0 if refunded else hours
    return out
def _menu_stats(chat_id, message_id=None):
    s = _service_stats_snapshot()
    lines = ['📊 <b>Статистика</b>', '', f"🛒 Всего заказов: <b>{s['total']}</b>", f"🚀 Активных: <b>{s['active']}</b>", f"✅ Завершено: <b>{s['completed']}</b>", f"↩️ Возвратов: <b>{s['refunded']}</b>", f"📦 Продано единиц: <b>{s['units']}</b>", f"⏱ Продано времени: <b>{s['hours']:g} ч.</b>"]
    if s['lots']:
        lines.append('\n<b>По лотам:</b>')
        for lot_id, row in sorted(s['lots'].items(), key=lambda x: -x[1]['orders'])[:20]:
            lines.append(f"• <code>{html.escape(lot_id)}</code>: {row['orders']} зак. / {row['hours']:g} ч.")
    kb = _make_kb([[('🗑 Сбросить статистику', 'sfp_stats_reset_ask')], [('◀️ Назад', 'sfp_main')]])
    _tg_edit(chat_id, message_id, '\n'.join(lines), kb) if message_id else _tg_send(chat_id, '\n'.join(lines), kb)
def _lot_title(value, lot_id):
    for key in ('title_ru', 'title', 'name', 'description'):
        raw = _object_value(value, key)
        if raw:
            return re.sub('\\s+', ' ', str(raw)).strip()[:120]
    return f'LOT {lot_id}'
def _validate_funpay_lot(lot_id):
    lot_id = str(lot_id or '').strip()
    if not lot_id.isdigit() or int(lot_id) <= 0:
        raise ValueError('Некорректный LOT ID')
    if cardinal is None or getattr(cardinal, 'account', None) is None:
        raise ValueError('FunPay ещё не инициализирован')
    fields = cardinal.account.get_lot_fields(int(lot_id))
    return {'lot_id': lot_id, 'title': _lot_title(fields, lot_id), 'active': bool(getattr(fields, 'active', True))}
def _discover_funpay_lots():
    global _farm_discovery_cache
    if cardinal is None or getattr(cardinal, 'account', None) is None:
        raise ValueError('FunPay ещё не инициализирован')
    found = {}
    errors = []
    for category in AUTO_LOT_CATEGORIES:
        try:
            for lot in cardinal.account.get_my_subcategory_lots(int(category)) or []:
                lot_id = _lot_id_text(_object_value(lot, 'id'))
                if lot_id:
                    found[lot_id] = {'lot_id': lot_id, 'title': _lot_title(lot, lot_id), 'active': bool(_object_value(lot, 'active') if _object_value(lot, 'active') is not None else True)}
        except Exception as e:
            errors.append(f'{category}: {str(e)[:100]}')
    for lot_id, item in list(found.items()):
        try:
            item.update(_validate_funpay_lot(lot_id))
        except Exception:
            pass
    _farm_discovery_cache = dict(found)
    with _state_lock:
        configured = set(_bindings)
    return {'lots': list(found.values()), 'found': len(found), 'new': sum((1 for x in found if x not in configured)), 'errors': errors}
def _lot_live_capacity(binding):
    try:
        snap = _api_snapshot()
        return _capacity_for_binding(binding, snap['subscription'], _occupied_account_count(snap['accounts']))
    except Exception:
        return None
def _menu_lots(chat_id, message_id=None):
    with _state_lock:
        bindings = [(str(k), _normalize_binding(v)) for k, v in _bindings.items() if isinstance(v, dict)]
    lines = ['🎟 <b>Настройка лотов</b>', '']
    rows = [[('🔎 Автопоиск лотов', 'sfp_lots_discover'), ('➕ Добавить вручную', 'sfp_lot_add')]]
    if not bindings:
        lines.append('\nНастроенных лотов пока нет.')
    for lot_id, b in sorted(bindings, key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        cap = _lot_live_capacity(b)
        qty = '?' if cap is None else str(int(cap.get('sellable_qty', 0) or 0))
        status = '🟢' if b['enabled'] else '🔴'
        title = b['lot_name'] or f'LOT {lot_id}'
        game = 'покупатель' if b['game_policy'] == 'buyer' else ' '.join(map(str, b['fixed_games']))
        lines.append(f"\n{status} <b>{html.escape(title)}</b>\n<code>{lot_id}</code> · {b['hours_per_unit']:g} ч/шт · игр ≤ {b['max_games']} · игра: {html.escape(game)} · можно {qty}")
        rows.append([(f"{status} {lot_id} · {b['hours_per_unit']:g} ч.", f'sfp_lot:{lot_id}')])
    rows.extend([[('🔄 Пересчитать все', 'sfp_lots_sync')], [('◀️ Назад', 'sfp_main')]])
    _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb(rows)) if message_id else _tg_send(chat_id, '\n'.join(lines), _make_kb(rows))
def _menu_lot_detail(chat_id, message_id, lot_id):
    with _state_lock:
        raw = _bindings.get(str(lot_id))
    if not isinstance(raw, dict):
        _menu_lots(chat_id, message_id)
        return
    b = _normalize_binding(raw)
    cap = _lot_live_capacity(b)
    qty = '?' if cap is None else int(cap.get('sellable_qty', 0) or 0)
    reason = '' if cap is None or cap.get('ok') else _capacity_reason_text(cap.get('reason'))
    try:
        lf = cardinal.account.get_lot_fields(int(lot_id)) if cardinal and getattr(cardinal, 'account', None) else None
        active = bool(getattr(lf, 'active', False)) if lf is not None else None
    except Exception:
        active = None
    state = '🔴 выключен' if not b['enabled'] else '🟢 включён' if active is True else '🟠 авто-пауза' if active is False and cap is not None and (not cap.get('ok')) else '🟡 синхронизация' if active is False else '⚪️ неизвестно'
    game = 'выбирает покупатель' if b['game_policy'] == 'buyer' else 'задано продавцом: ' + ' '.join(map(str, b['fixed_games']))
    text = f"🎟 <b>{html.escape(b['lot_name'] or f'LOT {lot_id}')}</b>\n\nLOT ID: <code>{html.escape(str(lot_id))}</code>\nСостояние лота: <b>{state}</b>\n⏱ За 1 покупку: <b>{b['hours_per_unit']:g} ч.</b>\n🎮 Максимум игр: <b>{b['max_games']}</b>\n🎯 Игра: <b>{html.escape(game)}</b>\n👻 Скрытый онлайн: <b>{('да' if b['hidden'] else 'нет')}</b>\n📦 Можно продать сейчас: <b>{qty}</b>"
    if reason:
        text += f'\n⚠️ {html.escape(reason)}'
    toggle = '🔴 Выключить лот' if b['enabled'] else '🟢 Включить лот'
    kb = _make_kb([[(toggle, f'sfp_lot_toggle:{lot_id}')], [('⏱ Время за 1 покупку', f'sfp_lot_hours:{lot_id}'), ('🎮 Максимум игр', f'sfp_lot_games:{lot_id}')], [('🎯 Кто выбирает игру', f'sfp_lot_policy:{lot_id}')], [(f"👻 Скрытый онлайн: {('ВКЛ' if b['hidden'] else 'ВЫКЛ')}", f'sfp_lot_hidden:{lot_id}')], [('🔄 Пересчитать', f'sfp_lot_sync:{lot_id}'), ('🗑 Удалить', f'sfp_lot_delask:{lot_id}')], [('◀️ Назад', 'sfp_lots')]])
    _tg_edit(chat_id, message_id, text, kb)
def _menu_lot_policy(chat_id, message_id, lot_id):
    with _state_lock:
        raw = _bindings.get(str(lot_id))
    if not isinstance(raw, dict):
        _menu_lots(chat_id, message_id)
        return
    b = _normalize_binding(raw)
    current = 'покупатель' if b['game_policy'] == 'buyer' else 'продавец: ' + ' '.join(map(str, b['fixed_games']))
    text = f'🎯 <b>Игра для лота {html.escape(str(lot_id))}</b>\n\nСейчас: <b>{html.escape(current)}</b>'
    kb = _make_kb([[('👤 Выбирает покупатель', f'sfp_lot_policy_buyer:{lot_id}')], [('🎮 Задаёт продавец', f'sfp_lot_policy_fixed:{lot_id}')], [('◀️ Назад', f'sfp_lot:{lot_id}')]])
    _tg_edit(chat_id, message_id, text, kb)
def _menu_discovery(chat_id, message_id, report):
    with _state_lock:
        configured = set(_bindings)
    lines = ['🔎 <b>Автопоиск лотов</b>', '', f"Найдено: <b>{report.get('found', 0)}</b> · новых: <b>{report.get('new', 0)}</b>"]
    rows = []
    for item in report.get('lots') or []:
        lot_id = str(item.get('lot_id') or '')
        mark = '✅' if lot_id in configured else '➕'
        rows.append([(f"{mark} {str(item.get('title') or lot_id)[:36]} · {lot_id}"[:60], f'sfp_lot:{lot_id}' if lot_id in configured else f'sfp_lot_found:{lot_id}')])
    if report.get('errors'):
        lines.append('\n⚠️ ' + html.escape(' | '.join(report['errors'])[:300]))
    rows.append([('🔄 Искать снова', 'sfp_lots_discover'), ('◀️ К лотам', 'sfp_lots')])
    _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb(rows))
def _menu_maintenance(chat_id, message_id=None):
    size = Path(LOG_FILE).stat().st_size if Path(LOG_FILE).exists() else 0
    text = f'🧰 <b>Обслуживание</b>\n\n📄 Лог: <code>{size} байт</code>\n📂 Данные: <code>{html.escape(STORAGE_DIR)}</code>'
    kb = _make_kb([[('📄 Логи', 'sfp_logs')], [('💾 Конфиг', 'sfp_config')], [('◀️ Назад', 'sfp_plugin_settings')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_logs(chat_id, message_id=None):
    tail = 'Лог пока пуст.'
    try:
        if Path(LOG_FILE).exists():
            tail = '\n'.join(Path(LOG_FILE).read_text(encoding='utf-8', errors='replace').splitlines()[-20:])[-2800:] or tail
    except Exception as e:
        tail = f'Не удалось прочитать лог: {e}'
    text = f'📄 <b>Логи</b>\n\n<code>{html.escape(tail)}</code>'
    kb = _make_kb([[('📥 Скачать лог', 'sfp_logs_download')], [('🗑 Очистить лог', 'sfp_logs_clear_ask')], [('◀️ Назад', 'sfp_maintenance')]])
    _tg_edit(chat_id, message_id, text, kb)
def _menu_config(chat_id, message_id=None):
    text = '💾 <b>Конфиг</b>\n\nСкачать — сохранить настройки, сообщения и лоты. Импортировать — восстановить их из JSON.\n\n⚠️ В файле находится API-ключ.'
    kb = _make_kb([[('📤 Скачать конфиг', 'sfp_config_export'), ('📥 Импортировать', 'sfp_config_import')], [('◀️ Назад', 'sfp_maintenance')]])
    _tg_edit(chat_id, message_id, text, kb)
def _menu_info(chat_id, message_id=None):
    text = 'ℹ️ <b>Информация</b>\n\nСлева — официальный сервис dim4n4ik.shop. Справа — инструкция, чат, канал и GitHub плагина.'
    kb = _make_kb([[('📖 Инструкция', INSTRUCTION_URL), ('📚 GitHub-инструкция', ALT_INSTRUCTION_URL)], [('🎮 Steam-магазин', SHOP_BOT_URL), ('💬 Чат плагина', GROUP_URL)], [('💬 Чат магазина', SHOP_CHAT_URL), ('📢 Канал', CHANNEL_URL)], [('🌐 Сайт', SHOP_SITE_URL), ('💻 GitHub', GITHUB_URL)], [('👤 Создатель сервиса', SERVICE_AUTHOR_URL), ('👨\u200d💻 Разработчик', CREATOR_URL)], [('◀️ Назад', 'sfp_home')]])
    if message_id:
        _tg_edit(chat_id, message_id, text, kb)
    else:
        _tg_send(chat_id, text, kb)
def _config_export_payload():
    with _config_lock:
        settings = {k: copy.deepcopy(_config.get(k, v)) for k, v in DEFAULT_CONFIG.items()}
    with _state_lock:
        lots = {str(k): _normalize_binding(v) for k, v in _bindings.items() if isinstance(v, dict)}
    return {'schema': 2, 'uuid': UUID, 'version': VERSION, 'exported_at': datetime.now().isoformat(timespec='seconds'), 'settings': settings, 'lots': lots}
def _validate_config_import(payload):
    if not isinstance(payload, dict):
        raise ValueError('Корень конфига должен быть JSON-объектом')
    if int(payload.get('schema', 0) or 0) not in (1, 2):
        raise ValueError('Неподдерживаемая версия конфига')
    if str(payload.get('uuid') or '') != UUID:
        raise ValueError('UUID конфига не совпадает')
    settings = payload.get('settings')
    lots = payload.get('lots')
    if not isinstance(settings, dict) or not isinstance(lots, dict):
        raise ValueError('В конфиге отсутствуют settings или lots')
    clean = copy.deepcopy(DEFAULT_CONFIG)
    for key in clean:
        if key in settings:
            clean[key] = settings[key]
    merged = copy.deepcopy(DEFAULT_MESSAGES)
    if isinstance(clean.get('messages'), dict):
        for key, value in clean['messages'].items():
            if key in merged and isinstance(value, str) and value.strip():
                merged[key] = _validate_message_template(value)
    clean['messages'] = merged
    out = {}
    for lot_id, raw in lots.items():
        if not str(lot_id).isdigit() or not isinstance(raw, dict):
            raise ValueError(f'Некорректный лот: {lot_id}')
        item = _normalize_binding(raw)
        item['lot_id'] = str(lot_id)
        out[str(lot_id)] = item
    return {'settings': clean, 'lots': out}
def _export_config_document(chat_id):
    _ensure_dirs()
    path = Path(LOG_DIR) / f'steam-farm-config-{int(time.time())}.json'
    try:
        _atomic_json(path, _config_export_payload())
        return _send_document(chat_id, str(path), '💾 Конфиг Steam Farm Hours. ⚠️ Содержит API-ключ.')
    finally:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
def _version_key(value):
    nums = [int(x) for x in re.findall('\\d+', str(value or ''))[:4]]
    return tuple((nums + [0] * 4)[:4])
def _version_from_source(source):
    match = re.search('(?m)^\\s*VERSION\\s*=\\s*["\\\']([^"\\\']+)["\\\']', source or '')
    return match.group(1).strip() if match else None
def _validate_update(payload):
    if not payload or len(payload) < 1000:
        raise RuntimeError('файл обновления слишком маленький')
    if len(payload) > 5 * 1024 * 1024:
        raise RuntimeError('файл обновления слишком большой')
    source = payload.decode('utf-8-sig')
    required = (UUID, 'BIND_TO_PRE_INIT', 'BIND_TO_NEW_ORDER', 'BIND_TO_NEW_MESSAGE')
    if any((x not in source for x in required)):
        raise RuntimeError('файл не похож на этот плагин')
    version = _version_from_source(source)
    if not version:
        raise RuntimeError('VERSION не найдена')
    if _version_key(version) <= _version_key(VERSION):
        raise RuntimeError(f'версия {version} не новее установленной {VERSION}')
    compile(source, str(Path(__file__).resolve()), 'exec')
    return (source, version)
def _download_online_update():
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': f'steam-farm-cardinal/{VERSION}'}
    meta = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}', headers=headers, timeout=20)
    meta.raise_for_status()
    branch = str((meta.json() or {}).get('default_branch') or 'main')
    tree = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}/git/trees/{branch}?recursive=1', headers=headers, timeout=25)
    tree.raise_for_status()
    paths = [str(x.get('path')) for x in (tree.json() or {}).get('tree', []) if x.get('type') == 'blob' and str(x.get('path', '')).lower().endswith('.py')]
    for path in sorted(paths, key=lambda x: (0 if 'farm' in x.lower() else 1, len(x)))[:40]:
        url = f'https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/{path}'
        response = requests.get(url, headers={'User-Agent': headers['User-Agent']}, timeout=25)
        if response.status_code == 200 and UUID in response.text and ('BIND_TO_NEW_ORDER' in response.text):
            return (response.content, url)
    raise RuntimeError('не удалось найти новую версию в репозитории')
def _install_update(payload):
    plugin = Path(__file__).resolve()
    temporary = plugin.with_name(plugin.name + '.update.tmp')
    backup = plugin.with_name(plugin.name + '.pre-update.bak')
    try:
        _, version = _validate_update(payload)
        with temporary.open('wb') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        shutil.copy2(plugin, backup)
        os.replace(temporary, plugin)
        return {'ok': True, 'version': version, 'backup': backup.name}
    except Exception as e:
        try:
            temporary.unlink(missing_ok=True)
        except Exception:
            pass
        return {'ok': False, 'error': str(e)[:300]}
def _menu_update(chat_id, message_id=None):
    text = f'⬆️ <b>Обновление {NAME}</b>\n\nТекущая версия: <code>{VERSION}</code>'
    kb = _make_kb([[('🌐 Онлайн', 'sfp_update_online'), ('📥 Локально', 'sfp_update_local')], [('◀️ Назад', 'sfp_home')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _online_update_worker(chat_id, message_id):
    try:
        payload, source = _download_online_update()
        result = _install_update(payload)
        text = f"✅ Плагин обновлён до <code>{result['version']}</code>. Выполните <code>/restart</code>." if result.get('ok') else f"❌ Обновление не установлено.\n{html.escape(str(result.get('error') or 'ошибка'))}"
        _log_event('update_checked', source=source, ok=result.get('ok'))
    except Exception as e:
        text = f'❌ Не удалось проверить обновление.\n{html.escape(str(e)[:300])}'
    finally:
        if _update_lock.locked():
            _update_lock.release()
    _tg_edit(chat_id, message_id, text, _make_kb([[('◀️ Назад', 'sfp_update')]]))
def _start_online_update(chat_id, message_id):
    if not _update_lock.acquire(blocking=False):
        _tg_edit(chat_id, message_id, '⏳ Проверка обновления уже выполняется.', _make_kb([[('◀️ Назад', 'sfp_update')]]))
        return
    _tg_edit(chat_id, message_id, '⏳ Проверяю новую версию…', _make_kb([[('◀️ Назад', 'sfp_home')]]))
    threading.Thread(target=_online_update_worker, args=(chat_id, message_id), daemon=True).start()
def _wizard_prompt(chat_id, title, text, back='sfp_lots'):
    _tg_send(chat_id, f'{title}\n\n{text}', _make_kb([[('❌ Отмена', back)]]))
def _save_lot_wizard(chat_id):
    state = dict(_waiting.get(int(chat_id)) or {})
    lot_id = str(state.get('lot_id') or '')
    binding = _normalize_binding({'lot_id': lot_id, 'lot_name': state.get('lot_name') or '', 'hours_per_unit': state.get('hours_per_unit', 1), 'max_games': state.get('max_games', 1), 'hidden': state.get('hidden', False), 'game_policy': state.get('game_policy', 'buyer'), 'fixed_games': state.get('fixed_games') or [], 'enabled': True, 'manual_disabled': False})
    with _state_lock:
        _bindings[lot_id] = binding
    _waiting.pop(int(chat_id), None)
    _save_runtime_state()
    try:
        _capacity_check_once()
    except Exception:
        pass
    _menu_lot_detail(chat_id, None, lot_id)
def _admin_text_handler(message):
    chat_id = getattr(getattr(message, 'chat', None), 'id', None)
    user_id = getattr(getattr(message, 'from_user', None), 'id', None)
    if not chat_id or not _is_authorized(user_id):
        return
    state = dict(_waiting.get(int(chat_id)) or {})
    action = str(state.get('action') or '')
    text = str(getattr(message, 'text', '') or '').strip()
    if not action:
        return
    if action == 'api_key':
        if not text.startswith('rk_'):
            _tg_send(chat_id, '⚠️ Ключ должен начинаться с <code>rk_</code>.')
            return
        try:
            candidate = FarmClient(text)
            balance = candidate.get_balance_kop()
            candidate.get_subscription()
        except Exception as e:
            _tg_send(chat_id, f'❌ Ключ не сохранён: {html.escape(_human_error(e))}')
            return
        cfg_set('api_key', text)
        _waiting.pop(int(chat_id), None)
        _delete_user_message(message)
        _tg_send(chat_id, f'✅ API-ключ сохранён. Баланс: <b>{_fmt_rub(balance)}</b>')
        _menu_api(chat_id, live=False)
        return
    if action == 'local_accounts':
        try:
            value = int(text)
            assert 1 <= value <= 100
        except Exception:
            _tg_send(chat_id, '⚠️ Введите целое число от 1 до 100.')
            return
        cfg_set('local_max_accounts', value)
        _waiting.pop(int(chat_id), None)
        _tg_send(chat_id, f'✅ Лимит Local: <b>{value}</b> аккаунтов.')
        _menu_local(chat_id, live=False)
        return
    if action == 'local_games':
        try:
            value = int(text)
            assert 1 <= value <= 32
        except Exception:
            _tg_send(chat_id, '⚠️ Введите целое число от 1 до 32.')
            return
        cfg_set('local_max_games', value)
        _waiting.pop(int(chat_id), None)
        _tg_send(chat_id, f'✅ Максимум игр Local: <b>{value}</b>.')
        _menu_local(chat_id, live=False)
        return
    if action == 'lot_id':
        match = re.search('(?:id=)?(\\d+)', text)
        if not match:
            _tg_send(chat_id, '⚠️ Отправьте LOT ID числом или ссылку с id=12345.')
            return
        try:
            item = _validate_funpay_lot(match.group(1))
        except Exception as e:
            _tg_send(chat_id, f'❌ Лот недоступен: {html.escape(_human_error(e))}')
            return
        _waiting[int(chat_id)] = {'action': 'lot_hours', 'lot_id': item['lot_id'], 'lot_name': item['title']}
        _wizard_prompt(chat_id, '⏱ <b>Время за 1 покупку</b>', 'Введите количество часов, например <code>2</code>.')
        return
    if action == 'lot_hours':
        try:
            value = float(text.replace(',', '.'))
            assert 0.25 <= value <= 720
        except Exception:
            _tg_send(chat_id, '⚠️ Введите число от 0.25 до 720.')
            return
        state.update({'action': 'lot_games', 'hours_per_unit': value})
        _waiting[int(chat_id)] = state
        _wizard_prompt(chat_id, '🎮 <b>Максимум игр</b>', 'Введите количество игр от 1 до 32.')
        return
    if action == 'lot_games':
        try:
            value = int(text)
            assert 1 <= value <= 32
        except Exception:
            _tg_send(chat_id, '⚠️ Введите целое число от 1 до 32.')
            return
        state.update({'action': 'lot_hidden', 'max_games': value})
        _waiting[int(chat_id)] = state
        _tg_send(chat_id, '👻 <b>Скрытый онлайн</b>\n\nЗапускать аккаунт в скрытом режиме?', _make_kb([[('✅ Да', 'sfp_wizard_hidden_yes'), ('❌ Нет', 'sfp_wizard_hidden_no')], [('🚫 Отмена', 'sfp_lots')]]))
        return
    if action == 'lot_fixed_games':
        games = _normalize_appids(text, max(1, int(state.get('max_games') or 1)))
        if not games:
            _tg_send(chat_id, '⚠️ Укажите хотя бы один AppID.')
            return
        state.update({'game_policy': 'fixed', 'fixed_games': games})
        _waiting[int(chat_id)] = state
        _save_lot_wizard(chat_id)
        return
    if action == 'edit_hours':
        lot_id = str(state.get('lot_id') or '')
        try:
            value = float(text.replace(',', '.'))
            assert 0.25 <= value <= 720
        except Exception:
            _tg_send(chat_id, '⚠️ Введите число от 0.25 до 720.')
            return
        with _state_lock:
            if lot_id in _bindings:
                _bindings[lot_id]['hours_per_unit'] = value
        _waiting.pop(int(chat_id), None)
        _save_runtime_state()
        _menu_lot_detail(chat_id, None, lot_id)
        return
    if action == 'edit_games':
        lot_id = str(state.get('lot_id') or '')
        try:
            value = int(text)
            assert 1 <= value <= 32
        except Exception:
            _tg_send(chat_id, '⚠️ Введите целое число от 1 до 32.')
            return
        with _state_lock:
            if lot_id in _bindings:
                _bindings[lot_id]['max_games'] = value
                _bindings[lot_id]['fixed_games'] = _normalize_appids(_bindings[lot_id].get('fixed_games') or [], value)
        _waiting.pop(int(chat_id), None)
        _save_runtime_state()
        _menu_lot_detail(chat_id, None, lot_id)
        return
    if action == 'edit_fixed_games':
        lot_id = str(state.get('lot_id') or '')
        with _state_lock:
            b = _normalize_binding(_bindings.get(lot_id) or {})
        games = _normalize_appids(text, b['max_games'])
        if not games:
            _tg_send(chat_id, '⚠️ Укажите хотя бы один AppID.')
            return
        with _state_lock:
            raw = dict(_bindings.get(lot_id) or {})
            raw['game_policy'] = 'fixed'
            raw['fixed_games'] = games
            _bindings[lot_id] = _normalize_binding(raw)
        _waiting.pop(int(chat_id), None)
        _save_runtime_state()
        _menu_lot_detail(chat_id, None, lot_id)
        return
    if action == 'buffer':
        try:
            value = float(text.replace(',', '.'))
            assert 0 <= value <= 24
        except Exception:
            _tg_send(chat_id, '⚠️ Введите число от 0 до 24.')
            return
        cfg_set('safety_buffer_hours', value)
        _waiting.pop(int(chat_id), None)
        _menu_safety(chat_id)
        return
    if action == 'interval':
        try:
            value = int(text)
            assert 30 <= value <= 3600
        except Exception:
            _tg_send(chat_id, '⚠️ Введите целое число от 30 до 3600.')
            return
        cfg_set('capacity_check_sec', value)
        _waiting.pop(int(chat_id), None)
        _menu_safety(chat_id)
        return
    if action == 'message_edit':
        key = str(state.get('key') or '')
        try:
            value = _validate_message_template(text)
        except Exception as e:
            _tg_send(chat_id, f'⚠️ {html.escape(str(e))}')
            return
        messages = dict(cfg_get('messages') or DEFAULT_MESSAGES)
        messages[key] = value
        cfg_set('messages', messages)
        _waiting.pop(int(chat_id), None)
        _tg_send(chat_id, '✅ Сообщение сохранено.')
        _menu_message_detail(chat_id, None, key)
        return
def _document_handler(message):
    chat_id = getattr(getattr(message, 'chat', None), 'id', None)
    user_id = getattr(getattr(message, 'from_user', None), 'id', None)
    if not chat_id or not _is_authorized(user_id):
        return
    state = dict(_waiting.get(int(chat_id)) or {})
    action = str(state.get('action') or '')
    if action not in {'config_import', 'plugin_update'}:
        return
    document = getattr(message, 'document', None)
    filename = str(getattr(document, 'file_name', '') or '')
    try:
        info = bot.get_file(document.file_id)
        raw = bytes(bot.download_file(info.file_path))
    except Exception as e:
        _tg_send(chat_id, f'❌ Не удалось скачать файл: {html.escape(str(e)[:200])}')
        return
    if action == 'config_import':
        if not filename.lower().endswith('.json'):
            _tg_send(chat_id, '❌ Нужен JSON-файл.')
            return
        try:
            clean = _validate_config_import(json.loads(raw.decode('utf-8-sig')))
            backup = Path(LOG_DIR) / f'config-before-import-{int(time.time())}.json'
            _atomic_json(backup, _config_export_payload())
            with _config_lock:
                _config.clear()
                _config.update(clean['settings'])
                _save_config()
            with _state_lock:
                _bindings.clear()
                _bindings.update(clean['lots'])
            _waiting.pop(int(chat_id), None)
            _save_runtime_state()
            _invalidate_snapshot()
            _tg_send(chat_id, f'✅ Конфиг импортирован. Резервная копия: <code>{html.escape(backup.name)}</code>')
            _menu_config(chat_id)
        except Exception as e:
            _tg_send(chat_id, f'❌ Импорт не выполнен: {html.escape(_human_error(e))}')
            return
    else:
        if not filename.lower().endswith('.py'):
            _tg_send(chat_id, '❌ Нужен файл .py.')
            return
        result = _install_update(raw)
        _waiting.pop(int(chat_id), None)
        _tg_send(chat_id, f"✅ Обновление установлено: {result['version']}. Выполните <code>/restart</code>." if result.get('ok') else f"❌ {html.escape(str(result.get('error') or 'ошибка'))}")
def _health(chat_id, message_id, backend=None):
    mode = str(backend or _backend_mode()).lower()
    if mode == 'local':
        lines = ['🩺 <b>Проверка Local</b>', '']
        status = _local_runtime_status(live=False)
        lines.append(f"{'✅' if status.get('node') else '⚪️'} Node.js: {'готов' if status.get('node') else 'будет установлен автоматически'}")
        lines.append(f"{'✅' if status.get('installed') else '❌'} steam-user: {'установлен' if status.get('installed') else 'не установлен'}")
        if status.get('installed') and status.get('node'):
            try:
                t = time.monotonic()
                pong = _start_local_daemon()
                lines.append(f"✅ Helper: {int((time.monotonic() - t) * 1000)} мс · steam-user {html.escape(str(pong.get('version') or '?'))}")
                accounts = _local_direct_request('GET', '/sessions', timeout=3).get('data') or []
                lines.append(f"✅ Steam-аккаунты: {len(accounts)}")
            except Exception as e:
                lines.append(f"❌ Helper: {html.escape(_human_error(e))}")
        _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb([[('◀️ Назад', 'sfp_local')]]))
        return
    client = _get_api_client()
    if not client:
        _menu_api(chat_id, message_id, live=False)
        return
    lines = ['🩺 <b>Проверка API</b>', '']
    try:
        t = time.monotonic()
        pong = client.ping()
        lines.append(f"✅ Ping: {int((time.monotonic() - t) * 1000)} мс · v{html.escape(str(pong.get('version') or '?'))}")
    except Exception as e:
        lines.append(f'❌ Ping: {html.escape(_human_error(e))}')
    try:
        lines.append(f'✅ Баланс: {_fmt_rub(client.get_balance_kop())}')
    except Exception as e:
        lines.append(f'❌ Баланс: {html.escape(_human_error(e))}')
    try:
        accounts = client.get_accounts()
        lines.append(f"✅ Steam-аккаунты: {len(accounts)}")
    except Exception as e:
        lines.append(f'❌ Аккаунты: {html.escape(_human_error(e))}')
    _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb([[('◀️ Назад', 'sfp_api')]]))
def _callback_router(call):
    data = str(getattr(call, 'data', '') or '')
    chat_id = getattr(getattr(getattr(call, 'message', None), 'chat', None), 'id', None)
    message_id = getattr(getattr(call, 'message', None), 'message_id', None)
    user_id = getattr(getattr(call, 'from_user', None), 'id', None)
    if not data.startswith('sfp_') or not chat_id or (not _is_authorized(user_id)):
        return
    if data == 'sfp_home':
        _ack(call)
        _plugin_home(chat_id, message_id)
        return
    if data == 'sfp_main':
        _ack(call)
        _menu_main(chat_id, message_id)
        return
    if data == 'sfp_info':
        _ack(call)
        _menu_info(chat_id, message_id)
        return
    if data == 'sfp_backend':
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_backend(chat_id, message_id)
        return
    if data in {'sfp_backend_api', 'sfp_backend_local'}:
        target = 'api' if data.endswith('_api') else 'local'
        ok, reason = _switch_backend(target)
        if not ok:
            _ack(call, 'Переключение недоступно')
            _tg_send(chat_id, f'⚠️ {html.escape(reason)}')
            _menu_backend(chat_id, message_id)
            return
        _ack(call, 'Движок переключён')
        if target == 'local':
            _menu_local(chat_id, message_id, live=False)
        else:
            _menu_api(chat_id, message_id, live=False)
        return
    if data == 'sfp_local':
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_local(chat_id, message_id)
        return
    if data == 'sfp_local_install':
        _ack(call, 'Устанавливаю…')
        _tg_edit(chat_id, message_id, '📦 <b>Установка Local backend</b>\n\n⏳ Установка запущена. Node.js будет найден или скачан автоматически, затем установится steam-user.\n\nПодробный прогресс смотрите в терминале Cardinal.', _make_kb([[('◀️ Назад', 'sfp_local')]]))
        threading.Thread(target=_local_install_worker, args=(int(chat_id), message_id), daemon=True, name='steamfarm-local-install').start()
        return
    if data == 'sfp_local_restart':
        _ack(call, 'Перезапускаю…')
        try:
            _stop_local_daemon()
            _start_local_daemon(force=True)
            _tg_send(chat_id, '✅ Local helper перезапущен.')
        except Exception as e:
            _tg_send(chat_id, f'❌ {html.escape(_human_error(e))}')
        _menu_local(chat_id, message_id, live=False)
        return
    if data == 'sfp_local_health':
        _ack(call, 'Проверяю…')
        _health(chat_id, message_id, 'local')
        return
    if data == 'sfp_local_accounts':
        _ack(call)
        _waiting[int(chat_id)] = {'action': 'local_accounts'}
        _tg_edit(chat_id, message_id, f"👤 <b>Лимит аккаунтов Local</b>\n\nСейчас: <b>{int(cfg_get('local_max_accounts') or 3)}</b>\nВведите число от 1 до 100.", _make_kb([[('❌ Отмена', 'sfp_local')]]))
        return
    if data == 'sfp_local_games':
        _ack(call)
        _waiting[int(chat_id)] = {'action': 'local_games'}
        _tg_edit(chat_id, message_id, f"🎮 <b>Лимит игр Local</b>\n\nСейчас: <b>{int(cfg_get('local_max_games') or 32)}</b>\nВведите число от 1 до 32.", _make_kb([[('❌ Отмена', 'sfp_local')]]))
        return
    if data == 'sfp_api':
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_api(chat_id, message_id)
        return
    if data == 'sfp_setkey':
        _ack(call)
        _waiting[int(chat_id)] = {'action': 'api_key'}
        _tg_edit(chat_id, message_id, '🔑 <b>API-ключ</b>\n\nОтправьте ключ <code>rk_...</code>. Сообщение с ключом будет удалено после проверки.', _make_kb([[('❌ Отмена', 'sfp_api')]]))
        return
    if data == 'sfp_keydel_ask':
        _ack(call)
        _tg_edit(chat_id, message_id, '⚠️ <b>Удалить API-ключ?</b>', _make_kb([[('✅ Удалить', 'sfp_keydel_yes'), ('❌ Отмена', 'sfp_api')]]))
        return
    if data == 'sfp_keydel_yes':
        _ack(call, 'Удалён')
        cfg_set('api_key', '')
        _menu_api(chat_id, message_id, False)
        return
    if data in {'sfp_health', 'sfp_api_health'}:
        _ack(call, 'Проверяю…')
        _health(chat_id, message_id, 'api')
        return
    if data == 'sfp_subscription':
        _ack(call)
        _menu_subscription(chat_id, message_id)
        return
    if data == 'sfp_plans':
        _ack(call)
        _menu_plans(chat_id, message_id)
        return
    if data.startswith('sfp_plan:'):
        _ack(call)
        code = data.split(':', 1)[1]
        plan = _plan_by_code(code)
        if not plan:
            _tg_edit(chat_id, message_id, '❌ Тариф не найден.', _make_kb([[('◀️ Назад', 'sfp_plans')]]))
            return
        if code == 'trial' or int(plan.get('price_kop', 0) or 0) == 0:
            _prepare_purchase(chat_id, plan, 1, message_id)
        else:
            _menu_plan_periods(chat_id, message_id, plan)
        return
    if data.startswith('sfp_plan_period:'):
        _ack(call)
        parts = data.split(':')
        code = parts[1] if len(parts) > 1 else ''
        try:
            months = int(parts[2])
            assert months in PERIOD_DISCOUNTS
        except Exception:
            _menu_plans(chat_id, message_id)
            return
        plan = _plan_by_code(code)
        _prepare_purchase(chat_id, plan, months, message_id) if plan else _menu_plans(chat_id, message_id)
        return
    if data.startswith('sfp_subbuy:'):
        nonce = data.split(':', 1)[1]
        state = _purchase_confirm.get(int(chat_id))
        if not state or state.get('nonce') != nonce or time.time() - float(state.get('created_at', 0) or 0) > 1800:
            _ack(call, 'Подтверждение устарело')
            _purchase_confirm.pop(int(chat_id), None)
            _menu_subscription(chat_id, message_id)
            return
        client = _get_api_client()
        if not client:
            _ack(call, 'API-ключ не задан')
            return
        _ack(call, 'Покупаю…')
        try:
            result = client.buy_subscription(state['plan'], state['months'], state['accounts'], state['idem_key'])
            _purchase_confirm.pop(int(chat_id), None)
            _invalidate_snapshot()
            _tg_edit(chat_id, message_id, f"✅ <b>Подписка оформлена.</b>\n\nТариф: {html.escape(str(result.get('plan_name') or result.get('plan') or state['plan']))}\nСтоимость: {_fmt_rub(result.get('cost_kop', 0))}", _make_kb([[('💳 К подписке', 'sfp_subscription')]]))
        except Exception as e:
            _tg_edit(chat_id, message_id, f'❌ Покупка не выполнена.\n{html.escape(_human_error(e))}', _make_kb([[('🔁 Повторить', f'sfp_subbuy:{nonce}')], [('◀️ Назад', 'sfp_subscription')]]))
        return
    if data == 'sfp_plugin_settings':
        _ack(call)
        _menu_plugin_settings(chat_id, message_id)
        return
    if data == 'sfp_plugin_state':
        _ack(call)
        _menu_plugin_state(chat_id, message_id)
        return
    if data == 'sfp_toggle_plugin':
        _ack(call)
        cfg_set('plugin_enabled', not bool(cfg_get('plugin_enabled')))
        _menu_plugin_state(chat_id, message_id)
        return
    if data == 'sfp_orders':
        _ack(call)
        _menu_orders(chat_id, message_id)
        return
    if data == 'sfp_services':
        _ack(call)
        _menu_services(chat_id, message_id)
        return
    if data == 'sfp_order_history':
        _ack(call)
        _menu_order_history(chat_id, message_id)
        return
    if data.startswith('sfp_service:'):
        _ack(call)
        _menu_service_detail(chat_id, message_id, data.split(':', 1)[1])
        return
    if data.startswith('sfp_history:'):
        _ack(call)
        _menu_service_detail(chat_id, message_id, data.split(':', 1)[1], 'sfp_order_history')
        return
    if data.startswith('sfp_service_stop:'):
        _ack(call, 'Останавливаю…')
        oid = data.split(':', 1)[1]
        with _state_lock:
            service = dict(_services.get(oid) or {})
        ok = _stop_service_now(oid, 'stopped_manual', 'manual')
        if ok:
            _fp_send(service.get('chat_id'), _buyer_message('stopped_manual', order_id=oid), str(service.get('buyer') or ''))
        else:
            _tg_send(chat_id, '⚠️ Движок не подтвердил остановку. Плагин продолжит повторные проверки.')
        _menu_service_detail(chat_id, message_id, oid)
        return
    if data.startswith('sfp_service_disconnect:'):
        _ack(call, 'Отключаю…')
        oid = data.split(':', 1)[1]
        with _state_lock:
            service = dict(_services.get(oid) or {})
        try:
            aid = int(service.get('api_account_id') or 0)
            client = _get_client()
            if not client or aid <= 0:
                raise ValueError('Аккаунт уже отключён')
            client.delete_account(aid)
            _invalidate_snapshot()
            with _state_lock:
                current = _services.get(oid)
                if current:
                    current['api_account_id'] = None
                    current['step'] = 'disconnected'
                    current['completed_at'] = time.time()
            _save_runtime_state()
        except Exception as e:
            _tg_send(chat_id, f'⚠️ {html.escape(_human_error(e))}')
        _menu_service_detail(chat_id, message_id, oid)
        return
    if data == 'sfp_toggle_refund':
        _ack(call)
        cfg_set('auto_refund_enabled', not bool(cfg_get('auto_refund_enabled')))
        _menu_orders(chat_id, message_id)
        return
    if data == 'sfp_toggle_slot_deactivate':
        _ack(call)
        cfg_set('auto_deactivate_on_slots', not bool(cfg_get('auto_deactivate_on_slots')))
        _capacity_check_once()
        _menu_orders(chat_id, message_id)
        return
    if data == 'sfp_notifications':
        _ack(call)
        _menu_notifications(chat_id, message_id)
        return
    if data.startswith('sfp_ntgl:'):
        _ack(call)
        key = data.split(':', 1)[1]
        allowed = {'notifications_enabled', 'notify_new_order', 'notify_started', 'notify_completed', 'notify_errors', 'notify_subscription', 'notify_capacity', 'notify_reconnect'}
        if key in allowed:
            cfg_set(key, not bool(cfg_get(key)))
        _menu_notifications(chat_id, message_id)
        return
    if data == 'sfp_messages':
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_messages(chat_id, message_id)
        return
    if data.startswith('sfp_msg_edit:'):
        _ack(call)
        key = data.split(':', 1)[1]
        if key not in DEFAULT_MESSAGES:
            _menu_messages(chat_id, message_id)
            return
        _waiting[int(chat_id)] = {'action': 'message_edit', 'key': key}
        _tg_edit(chat_id, message_id, f'✏️ <b>{html.escape(MESSAGE_LABELS[key])}</b>\n\nОтправьте новый текст одним сообщением. Переменные в фигурных скобках можно оставить.', _make_kb([[('❌ Отмена', f'sfp_msg:{key}')]]))
        return
    if data.startswith('sfp_msg_reset:'):
        _ack(call, 'Сброшено')
        key = data.split(':', 1)[1]
        messages = dict(cfg_get('messages') or DEFAULT_MESSAGES)
        if key in DEFAULT_MESSAGES:
            messages[key] = DEFAULT_MESSAGES[key]
            cfg_set('messages', messages)
        _menu_message_detail(chat_id, message_id, key)
        return
    if data.startswith('sfp_msg:'):
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_message_detail(chat_id, message_id, data.split(':', 1)[1])
        return
    if data == 'sfp_messages_reset_ask':
        _ack(call)
        _tg_edit(chat_id, message_id, '⚠️ Сбросить все сообщения покупателю?', _make_kb([[('✅ Сбросить', 'sfp_messages_reset_yes'), ('❌ Отмена', 'sfp_messages')]]))
        return
    if data == 'sfp_messages_reset_yes':
        _ack(call, 'Сброшено')
        cfg_set('messages', copy.deepcopy(DEFAULT_MESSAGES))
        _menu_messages(chat_id, message_id)
        return
    if data == 'sfp_safety':
        _ack(call)
        _menu_safety(chat_id, message_id)
        return
    if data == 'sfp_set_buffer':
        _ack(call)
        _waiting[int(chat_id)] = {'action': 'buffer'}
        _tg_edit(chat_id, message_id, '🛡 Введите запас подписки в часах от 0 до 24.', _make_kb([[('❌ Отмена', 'sfp_safety')]]))
        return
    if data == 'sfp_set_interval':
        _ack(call)
        _waiting[int(chat_id)] = {'action': 'interval'}
        _tg_edit(chat_id, message_id, '⏱ Введите интервал проверки от 30 до 3600 секунд.', _make_kb([[('❌ Отмена', 'sfp_safety')]]))
        return
    if data == 'sfp_toggle_queue':
        _ack(call)
        cfg_set('queue_enabled', not bool(cfg_get('queue_enabled')))
        _promote_queue()
        _menu_safety(chat_id, message_id)
        return
    if data == 'sfp_toggle_expiry':
        _ack(call)
        cfg_set('notify_near_expiry', not bool(cfg_get('notify_near_expiry')))
        _menu_safety(chat_id, message_id)
        return
    if data == 'sfp_stats':
        _ack(call)
        _menu_stats(chat_id, message_id)
        return
    if data == 'sfp_stats_reset_ask':
        _ack(call)
        _tg_edit(chat_id, message_id, '⚠️ Сбросить статистику? История заказов не удалится.', _make_kb([[('✅ Сбросить', 'sfp_stats_reset_yes'), ('❌ Отмена', 'sfp_stats')]]))
        return
    if data == 'sfp_stats_reset_yes':
        _ack(call, 'Сброшено')
        cfg_set('stats_reset_at', time.time())
        _menu_stats(chat_id, message_id)
        return
    if data == 'sfp_lots':
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_lots(chat_id, message_id)
        return
    if data == 'sfp_lot_add':
        _ack(call)
        _waiting[int(chat_id)] = {'action': 'lot_id'}
        _tg_edit(chat_id, message_id, '➕ <b>Добавление лота</b>\n\nОтправьте LOT ID или ссылку на редактирование лота.', _make_kb([[('❌ Отмена', 'sfp_lots')]]))
        return
    if data == 'sfp_lots_discover':
        _ack(call, 'Ищу…')
        try:
            _menu_discovery(chat_id, message_id, _discover_funpay_lots())
        except Exception as e:
            _tg_edit(chat_id, message_id, f'❌ Автопоиск не выполнен: {html.escape(_human_error(e))}', _make_kb([[('◀️ Назад', 'sfp_lots')]]))
        return
    if data.startswith('sfp_lot_found:'):
        _ack(call)
        lot_id = data.split(':', 1)[1]
        item = dict(_farm_discovery_cache.get(lot_id) or {})
        if not item:
            try:
                item = _validate_funpay_lot(lot_id)
            except Exception as e:
                _tg_send(chat_id, f'❌ {html.escape(_human_error(e))}')
                return
        _waiting[int(chat_id)] = {'action': 'lot_hours', 'lot_id': lot_id, 'lot_name': item.get('title') or ''}
        _wizard_prompt(chat_id, '⏱ <b>Время за 1 покупку</b>', 'Введите количество часов, например <code>2</code>.')
        return
    if data in ('sfp_wizard_hidden_yes', 'sfp_wizard_hidden_no'):
        _ack(call)
        state = dict(_waiting.get(int(chat_id)) or {})
        if state.get('action') != 'lot_hidden':
            _menu_lots(chat_id, message_id)
            return
        state.update({'hidden': data.endswith('_yes'), 'action': 'lot_policy'})
        _waiting[int(chat_id)] = state
        _tg_edit(chat_id, message_id, '🎯 <b>Кто выбирает игру?</b>', _make_kb([[('👤 Покупатель', 'sfp_wizard_policy_buyer')], [('🎮 Продавец', 'sfp_wizard_policy_fixed')], [('🚫 Отмена', 'sfp_lots')]]))
        return
    if data == 'sfp_wizard_policy_buyer':
        _ack(call)
        state = dict(_waiting.get(int(chat_id)) or {})
        state.update({'game_policy': 'buyer', 'fixed_games': []})
        _waiting[int(chat_id)] = state
        _save_lot_wizard(chat_id)
        return
    if data == 'sfp_wizard_policy_fixed':
        _ack(call)
        state = dict(_waiting.get(int(chat_id)) or {})
        state['action'] = 'lot_fixed_games'
        _waiting[int(chat_id)] = state
        _tg_edit(chat_id, message_id, f"🎮 Отправьте AppID через пробел. Максимум: <b>{int(state.get('max_games') or 1)}</b>.", _make_kb([[('❌ Отмена', 'sfp_lots')]]))
        return
    if data == 'sfp_lots_sync':
        _ack(call, 'Пересчитываю…')
        _capacity_check_once()
        _menu_lots(chat_id, message_id)
        return
    if data.startswith('sfp_lot_toggle:'):
        lot_id = data.split(':', 1)[1]
        _ack(call, 'Синхронизация…')
        with _state_lock:
            original = dict(_bindings.get(lot_id) or {})
        if not original:
            _menu_lots(chat_id, message_id)
            return
        current = _normalize_binding(original)
        enabling = not current['enabled']
        if not enabling:
            with _state_lock:
                original.update({'enabled': False, 'manual_disabled': True})
                _bindings[lot_id] = _normalize_binding(original)
            _auto_disabled.pop(lot_id, None)
            _save_runtime_state()
            _set_funpay_lot_fields(lot_id, False, 0)
            _menu_lot_detail(chat_id, message_id, lot_id)
            return
        with _state_lock:
            original.update({'enabled': True, 'manual_disabled': False})
            _bindings[lot_id] = _normalize_binding(original)
            enabled = dict(_bindings[lot_id])
        _save_runtime_state()
        if not _set_funpay_lot_fields(lot_id, True, None):
            with _state_lock:
                original.update({'enabled': False, 'manual_disabled': True})
                _bindings[lot_id] = _normalize_binding(original)
            _save_runtime_state()
            _tg_send(chat_id, '❌ FunPay не подтвердил включение лота.')
            _menu_lot_detail(chat_id, message_id, lot_id)
            return
        try:
            snap = _api_snapshot(force=True)
            _sync_lot_capacity(lot_id, enabled, snap['subscription'], _occupied_account_count(snap['accounts']))
        except Exception as e:
            _set_funpay_lot_fields(lot_id, False, 0)
            with _state_lock:
                original.update({'enabled': False, 'manual_disabled': True})
                _bindings[lot_id] = _normalize_binding(original)
            _save_runtime_state()
            _tg_send(chat_id, f'❌ Лот не включён: не удалось синхронизировать движок. {html.escape(_human_error(e))}')
        _menu_lot_detail(chat_id, message_id, lot_id)
        return
    if data.startswith('sfp_lot_hours:'):
        _ack(call)
        lot_id = data.split(':', 1)[1]
        _waiting[int(chat_id)] = {'action': 'edit_hours', 'lot_id': lot_id}
        _tg_edit(chat_id, message_id, '⏱ Введите новое время за 1 покупку.', _make_kb([[('❌ Отмена', f'sfp_lot:{lot_id}')]]))
        return
    if data.startswith('sfp_lot_games:'):
        _ack(call)
        lot_id = data.split(':', 1)[1]
        _waiting[int(chat_id)] = {'action': 'edit_games', 'lot_id': lot_id}
        _tg_edit(chat_id, message_id, '🎮 Введите новый максимум игр от 1 до 32.', _make_kb([[('❌ Отмена', f'sfp_lot:{lot_id}')]]))
        return
    if data.startswith('sfp_lot_policy:'):
        _ack(call)
        _menu_lot_policy(chat_id, message_id, data.split(':', 1)[1])
        return
    if data.startswith('sfp_lot_policy_buyer:'):
        _ack(call)
        lot_id = data.split(':', 1)[1]
        with _state_lock:
            raw = dict(_bindings.get(lot_id) or {})
            raw.update({'game_policy': 'buyer', 'fixed_games': []})
            _bindings[lot_id] = _normalize_binding(raw)
        _save_runtime_state()
        _menu_lot_detail(chat_id, message_id, lot_id)
        return
    if data.startswith('sfp_lot_policy_fixed:'):
        _ack(call)
        lot_id = data.split(':', 1)[1]
        with _state_lock:
            b = _normalize_binding(_bindings.get(lot_id) or {})
        _waiting[int(chat_id)] = {'action': 'edit_fixed_games', 'lot_id': lot_id}
        _tg_edit(chat_id, message_id, f"🎮 Отправьте AppID через пробел. Максимум: <b>{b['max_games']}</b>.", _make_kb([[('❌ Отмена', f'sfp_lot:{lot_id}')]]))
        return
    if data.startswith('sfp_lot_hidden:'):
        _ack(call)
        lot_id = data.split(':', 1)[1]
        with _state_lock:
            if lot_id in _bindings:
                _bindings[lot_id]['hidden'] = not bool(_bindings[lot_id].get('hidden', False))
        _save_runtime_state()
        _menu_lot_detail(chat_id, message_id, lot_id)
        return
    if data.startswith('sfp_lot_sync:'):
        _ack(call, 'Пересчитываю…')
        lot_id = data.split(':', 1)[1]
        try:
            snap = _api_snapshot(force=True)
            with _state_lock:
                b = _normalize_binding(_bindings.get(lot_id) or {})
            _sync_lot_capacity(lot_id, b, snap['subscription'], _occupied_account_count(snap['accounts']))
        except Exception as e:
            _tg_send(chat_id, f'⚠️ {html.escape(_human_error(e))}')
        _menu_lot_detail(chat_id, message_id, lot_id)
        return
    if data.startswith('sfp_lot_delask:'):
        _ack(call)
        lot_id = data.split(':', 1)[1]
        _tg_edit(chat_id, message_id, f'Удалить привязку лота <code>{html.escape(lot_id)}</code>? Сам лот FunPay останется.', _make_kb([[('🗑 Да, удалить', f'sfp_lot_delete:{lot_id}')], [('❌ Отмена', f'sfp_lot:{lot_id}')]]))
        return
    if data.startswith('sfp_lot_delete:'):
        _ack(call, 'Удалено')
        lot_id = data.split(':', 1)[1]
        with _state_lock:
            _bindings.pop(lot_id, None)
            _auto_disabled.pop(lot_id, None)
        _save_runtime_state()
        _menu_lots(chat_id, message_id)
        return
    if data.startswith('sfp_lot:'):
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_lot_detail(chat_id, message_id, data.split(':', 1)[1])
        return
    if data == 'sfp_maintenance':
        _ack(call)
        _menu_maintenance(chat_id, message_id)
        return
    if data == 'sfp_logs':
        _ack(call)
        _menu_logs(chat_id, message_id)
        return
    if data == 'sfp_logs_download':
        _ack(call, 'Отправляю…')
        _send_document(chat_id, LOG_FILE, f'📄 Лог {NAME} {VERSION}') or _tg_send(chat_id, '⚠️ Лог пуст или недоступен.')
        return
    if data == 'sfp_logs_clear_ask':
        _ack(call)
        _tg_edit(chat_id, message_id, '⚠️ Очистить лог?', _make_kb([[('✅ Очистить', 'sfp_logs_clear_yes'), ('❌ Отмена', 'sfp_logs')]]))
        return
    if data == 'sfp_logs_clear_yes':
        _ack(call, 'Очищено')
        try:
            _close_logging()
            Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
            Path(LOG_FILE).write_text('', encoding='utf-8')
            _configure_logging()
        except Exception:
            pass
        _menu_logs(chat_id, message_id)
        return
    if data == 'sfp_config':
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_config(chat_id, message_id)
        return
    if data == 'sfp_config_export':
        _ack(call, 'Готовлю…')
        _export_config_document(int(chat_id))
        return
    if data == 'sfp_config_import':
        _ack(call)
        _waiting[int(chat_id)] = {'action': 'config_import'}
        _tg_edit(chat_id, message_id, '📥 Пришлите JSON-файл конфига.', _make_kb([[('❌ Отмена', 'sfp_config')]]))
        return
    if data == 'sfp_update':
        _ack(call)
        _waiting.pop(int(chat_id), None)
        _menu_update(chat_id, message_id)
        return
    if data == 'sfp_update_online':
        _ack(call, 'Проверяю…')
        _start_online_update(chat_id, message_id)
        return
    if data == 'sfp_update_local':
        _ack(call)
        _waiting[int(chat_id)] = {'action': 'plugin_update'}
        _tg_edit(chat_id, message_id, '📥 Пришлите новый файл <code>.py</code>.', _make_kb([[('❌ Отмена', 'sfp_update')]]))
        return
    if data == 'sfp_delete_ask':
        _ack(call)
        _tg_edit(chat_id, message_id, '⚠️ <b>Удалить плагин?</b>\n\nДанные в storage останутся.', _make_kb([[('🗑 Удалить', 'sfp_delete_do'), ('❌ Отмена', 'sfp_home')]]))
        return
    if data == 'sfp_delete_do':
        _ack(call)
        error = ''
        try:
            _stop_local_daemon()
        except Exception:
            pass
        try:
            Path(__file__).resolve().unlink()
        except Exception as e:
            error = str(e)
        _tg_edit(chat_id, message_id, '✅ Файл плагина удалён. Выполните <code>/restart</code>.' if not error else f'⚠️ {html.escape(error)}', _make_kb([[('🔙 К списку плагинов', CB_PLUGINS_LIST_OPEN)]]))
        return
    _ack(call)
_background_thread = None
def _register_handlers(c):
    def command_handler(message):
        global admin_chat_id
        chat_id = getattr(getattr(message, 'chat', None), 'id', None)
        user_id = getattr(getattr(message, 'from_user', None), 'id', None)
        if not chat_id or not _is_authorized(user_id):
            return
        if admin_chat_id is None:
            admin_chat_id = int(chat_id)
        _plugin_home(int(chat_id))
    def callback_handler(call):
        try:
            _callback_router(call)
        except Exception as e:
            _log_event('telegram_callback_error', level=logging.ERROR, action=str(getattr(call, 'data', '') or '')[:120], error=str(e))
            cid = getattr(getattr(getattr(call, 'message', None), 'chat', None), 'id', None)
            if cid:
                _tg_send(cid, f'❌ Ошибка плагина: {html.escape(str(e)[:180])}')
    try:
        register = getattr(getattr(c, 'telegram', None), 'msg_handler', None)
        predicate = lambda m: int(getattr(getattr(m, 'chat', None), 'id', 0) or 0) in _waiting
        if callable(register):
            register(_admin_text_handler, func=predicate, content_types=['text'])
        else:
            bot.register_message_handler(_admin_text_handler, func=predicate, content_types=['text'])
    except Exception as e:
        _log_event('telegram_text_handler_error', level=logging.WARNING, error=str(e))
    try:
        register = getattr(getattr(c, 'telegram', None), 'msg_handler', None)
        predicate = lambda m: str((_waiting.get(int(getattr(getattr(m, 'chat', None), 'id', 0) or 0)) or {}).get('action') or '') in {'config_import', 'plugin_update'}
        if callable(register):
            register(_document_handler, func=predicate, content_types=['document'])
        else:
            bot.register_message_handler(_document_handler, func=predicate, content_types=['document'])
    except Exception as e:
        _log_event('telegram_document_handler_error', level=logging.WARNING, error=str(e))
    try:
        bot.register_message_handler(command_handler, commands=['steamfarm'])
    except Exception as e:
        _log_event('telegram_command_handler_error', level=logging.WARNING, error=str(e))
    try:
        bot.register_callback_query_handler(callback_handler, func=lambda call: str(getattr(call, 'data', '') or '').startswith('sfp_'))
    except Exception as e:
        _log_event('telegram_callback_handler_error', level=logging.WARNING, error=str(e))
    if _CBT:
        def open_plugin(call):
            global admin_chat_id
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
            cid = getattr(getattr(getattr(call, 'message', None), 'chat', None), 'id', None)
            mid = getattr(getattr(call, 'message', None), 'message_id', None)
            if cid:
                if admin_chat_id is None:
                    admin_chat_id = int(cid)
                _plugin_home(int(cid), mid)
        def is_entry(data):
            value = str(data or '')
            if value in (CBT_SETTINGS, f'{UUID}:0'):
                return True
            edit = getattr(_CBT, 'EDIT_PLUGIN', None)
            settings = getattr(_CBT, 'PLUGIN_SETTINGS', None)
            return bool(edit is not None and value.startswith(f'{edit}:{UUID}') or (settings is not None and value.startswith(f'{settings}:{UUID}')))
        try:
            c.telegram.cbq_handler(open_plugin, func=lambda call: is_entry(getattr(call, 'data', None)))
        except Exception as e:
            _log_event('plugin_entry_handler_error', level=logging.WARNING, error=str(e))
def _migrate_runtime():
    with _state_lock:
        for lot_id, raw in list(_bindings.items()):
            if not isinstance(raw, dict):
                _bindings.pop(lot_id, None)
                continue
            item = dict(raw)
            item.pop('mode', None)
            item.pop('auto_manage', None)
            item.pop('auto_capacity', None)
            item['lot_id'] = str(lot_id)
            _bindings[str(lot_id)] = _normalize_binding(item)
        for oid, raw in list(_services.items()):
            if not isinstance(raw, dict):
                _services.pop(oid, None)
                continue
            item = _safe_service_for_save(raw)
            item.pop('mode', None)
            item.setdefault('backend', 'api')
            lot_id = str(item.get('lot_id') or '')
            binding = _bindings.get(lot_id)
            if isinstance(binding, dict):
                b = _normalize_binding(binding)
                item.setdefault('game_policy', b['game_policy'])
                item.setdefault('fixed_games', list(b['fixed_games']))
                item.setdefault('max_games', b['max_games'])
            _services[str(oid)] = item
def steamfarm_pre_init(c, *args):
    global cardinal, bot, admin_chat_id, _config, _client, _local_client, _bindings, _services, _auto_disabled, _notify_state, _background_thread
    _ensure_dirs()
    _configure_logging()
    _stop_event.clear()
    cardinal = c
    try:
        bot = getattr(c.telegram, 'bot', None)
    except Exception:
        bot = None
    with _config_lock:
        _config = _load_config()
        _save_config()
    _client = None
    _local_client = None
    _write_local_helper_files()
    _invalidate_snapshot()
    with _state_lock:
        _bindings = {str(k): dict(v) for k, v in _json_dict(BINDINGS_FILE).items() if isinstance(v, dict)}
        _services = {str(k): dict(v) for k, v in _json_dict(SERVICES_FILE).items() if isinstance(v, dict)}
        _auto_disabled = {str(k): float(v or 0) for k, v in _json_dict(AUTO_DISABLED_FILE).items()}
        _notify_state = _json_dict(NOTIFY_STATE_FILE)
    _migrate_runtime()
    _save_runtime_state()
    try:
        auth = getattr(getattr(c, 'telegram', None), 'authorized_users', None)
        admin_chat_id = int(next(iter(auth.keys()))) if isinstance(auth, dict) and auth else None
    except Exception:
        admin_chat_id = None
    try:
        c.add_telegram_commands(UUID, [('steamfarm', 'Steam Farm Hours: меню плагина', True)])
    except Exception as e:
        _log_event('add_command_error', level=logging.WARNING, error=str(e))
    if bot:
        _register_handlers(c)
    if _background_thread is None or not _background_thread.is_alive():
        _background_thread = threading.Thread(target=_background_loop, daemon=True, name='steamfarm-background')
        _background_thread.start()
    _log_event('initialized', version=VERSION, lots=len(_bindings), services=len(_services))
def on_delete(*args):
    _stop_event.set()
    try:
        _save_config()
        _save_runtime_state()
    except Exception:
        pass
    _waiting.clear()
    _purchase_confirm.clear()
    _log_event('deleted', version=VERSION)
    _close_logging()
BIND_TO_PRE_INIT = [steamfarm_pre_init]
BIND_TO_NEW_ORDER = [handle_new_order]
BIND_TO_NEW_MESSAGE = [handle_new_message]
BIND_TO_LAST_CHAT_MESSAGE_CHANGED = [handle_new_message]
BIND_TO_INIT_MESSAGE = [handle_new_message]
BIND_TO_ORDER_STATUS_CHANGED = [handle_order_status_changed]
BIND_TO_DELETE = [on_delete]