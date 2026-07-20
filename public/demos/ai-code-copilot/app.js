/* AI Code Copilot · 前端逻辑（纯前端演示，接口与 FastAPI :8003 同构） */
(function(){
  const $ = window.$;
  const $$ = window.$$;

  /* ---------- 极简语法高亮（仅用于展示） ---------- */
  function highlight(src){
    const esc = window.esc;
    const KW = new Set(['import','from','export','function','return','if','else','const','let','var',
      'try','catch','new','interface','type','class','extends','implements','for','of','in','as',
      'await','async','void','true','false','null','throw','rejects','describe','it','expect','default']);
    const re = /(\/\/[^\n]*)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)|\b([A-Za-z_$][\w$]*)\b|\b(\d+)\b/g;
    let out = '', last = 0, m;
    while((m = re.exec(src))){
      out += esc(src.slice(last, m.index));
      if(m[1]){
        out += '<span style="color:#64748b">' + esc(m[1]) + '</span>';
      } else if(m[2]){
        out += '<span style="color:#86efac">' + esc(m[2]) + '</span>';
      } else if(m[3]){
        const w = m[3];
        out += KW.has(w) ? '<span style="color:#c4b5fd">' + esc(w) + '</span>' : esc(w);
      } else if(m[4]){
        out += '<span style="color:#fbbf24">' + esc(m[4]) + '</span>';
      }
      last = re.lastIndex;
    }
    out += esc(src.slice(last));
    return out;
  }

  /* ---------- 关键词 → 场景路由 ---------- */
  function pickScenario(t){
    const s = t.toLowerCase();
    if(/jwt|鉴权|中间件|auth|token|登录|middleware/.test(s)) return 'jwt';
    if(/测试|单测|test|unittest|pytest|jest/.test(s)) return 'test';
    if(/排序|快排|sort|quicksort/.test(s)) return 'sort';
    if(/crud|增删改查|接口|controller|路由|api|服务/.test(s)) return 'crud';
    return 'default';
  }
  const SKILL = { gen:'codegen', refactor:'refactor', explain:'explain' };
  const INTENT = { gen:'代码生成', refactor:'代码重构', explain:'代码解释' };

  /* ---------- 硬编码响应表（按场景 × 动作区分产出） ---------- */
  const RESPONSES = {
    jwt: {
      gen: {
        note:'已生成 Express JWT 鉴权中间件（src/middleware/auth.ts）',
        stats:{lines:18, tests:'12/12', time:'1.8'},
        code:
`import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

const SECRET = process.env.JWT_SECRET ?? 'dev-secret';

export function authGuard(roles: string[] = []) {
  return (req: Request, res: Response, next: NextFunction) => {
    const header = req.headers.authorization ?? '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : '';
    if (!token) return res.status(401).json({ error: 'missing token' });
    try {
      const payload = jwt.verify(token, SECRET) as { sub: string; role: string };
      if (roles.length && !roles.includes(payload.role))
        return res.status(403).json({ error: 'forbidden' });
      req.user = payload;
      next();
    } catch {
      return res.status(401).json({ error: 'invalid token' });
    }
  };
}`
      },
      refactor: {
        note:'重构建议：提取常量、统一错误响应、角色校验内聚',
        stats:{lines:15, tests:'12/12', time:'1.2'},
        improvements:['提取 UNAUTH 统一错误体，避免重复字面量','用正则一次性剥离 Bearer 前缀','角色校验收拢进守卫工厂，便于复用'],
        code:
`// 重构后：更短、错误响应统一、支持角色
import { Request, Response, NextFunction } from 'express';
import jwt, { JwtPayload } from 'jsonwebtoken';

const SECRET = process.env.JWT_SECRET ?? 'dev-secret';
const UNAUTH = { error: 'unauthorized' };

export const authGuard = (roles: string[] = []) =>
  (req: Request, res: Response, next: NextFunction) => {
    const token = req.headers.authorization?.replace(/^Bearer\\s+/, '');
    if (!token) return res.status(401).json(UNAUTH);
    try {
      const user = jwt.verify(token, SECRET) as JwtPayload;
      if (roles.length && !roles.includes(user.role as string))
        return res.status(403).json({ error: 'forbidden' });
      req.user = user; next();
    } catch {
      res.status(401).json(UNAUTH);
    }
  };`
      },
      explain: {
        note:'已解释 JWT 鉴权中间件的工作流程',
        stats:{lines:'—', tests:'—', time:'0.4'},
        text:
`这是一个 Express **鉴权中间件工厂** \`authGuard\`：

- 从 \`Authorization\` 头提取 **Bearer Token**，缺失则返回 **401**；
- 用 \`jwt.verify\` 校验签名，失败同样返回 **401**；
- 若声明了 \`roles\`，校验角色，越权返回 **403**；
- 校验通过后把 \`payload\` 挂到 \`req.user\`，交给后续 handler。

核心是「**拦截 → 校验 → 放行**」的洋葱模型，可叠加到任意受保护路由。`
      }
    },

    test: {
      gen: {
        note:'已生成订单服务单元测试（order.service.spec.ts）',
        stats:{lines:21, tests:'9/9', time:'1.1'},
        code:
`import { describe, it, expect } from 'vitest';
import { createOrder } from './order.service';

describe('createOrder', () => {
  it('创建成功返回订单号', async () => {
    const order = await createOrder({ sku: 'A-1', qty: 2 });
    expect(order.id).toBeDefined();
    expect(order.status).toBe('created');
  });

  it('库存不足时抛错', async () => {
    await expect(createOrder({ sku: 'SOLD', qty: 999 }))
      .rejects.toThrow('insufficient stock');
  });
});`
      },
      refactor: {
        note:'重构建议：用工厂函数消除重复断言',
        stats:{lines:19, tests:'9/9', time:'0.9'},
        improvements:['抽出 \`makeOrder\` 工厂，避免每个用例重复构造','表驱动用例覆盖多组异常','统一断言风格'],
        code:
`import { describe, it, expect } from 'vitest';
import { createOrder } from './order.service';

const makeOrder = (over = {}) =>
  createOrder({ sku: 'A-1', qty: 2, ...over });

describe('createOrder', () => {
  it('创建成功返回订单号', async () => {
    const order = await makeOrder();
    expect(order.id).toBeDefined();
    expect(order.status).toBe('created');
  });
  it.each([
    ['SOLD', 999, 'insufficient stock'],
    ['BAD', -1, 'invalid qty'],
  ])('异常 %s/%i 抛 %s', async (sku, qty, msg) => {
    await expect(makeOrder({ sku, qty })).rejects.toThrow(msg);
  });
});`
      },
      explain: {
        note:'已解释单元测试的覆盖策略',
        stats:{lines:'—', tests:'—', time:'0.3'},
        text:
`这组测试采用 **AAA 模式**（Arrange / Act / Assert）：

- 正常路径：验证返回订单号与初始状态 \`created\`；
- 异常路径：用 \`rejects.toThrow\` 断言库存/参数错误的失败语义；
- 通过 \`describe\` 分组与 \`it\` 命名让意图一目了然，便于 CI 失败快速定位。`
      }
    },

    sort: {
      gen: {
        note:'已生成快速排序（quicksort.ts）',
        stats:{lines:9, tests:'7/7', time:'0.7'},
        code:
`export function quicksort<T>(arr: T[]): T[] {
  if (arr.length <= 1) return arr;
  const [pivot, ...rest] = arr;
  const left = rest.filter(x => x < pivot);
  const right = rest.filter(x => x >= pivot);
  return [...quicksort(left), pivot, ...quicksort(right)];
}`
      },
      refactor: {
        note:'重构建议：支持自定义比较器、原地分区',
        stats:{lines:14, tests:'7/7', time:'0.8'},
        improvements:['增加 \`compare\` 参数支持任意类型排序','改用原地分区降低空间占用','空/单元素提前返回'],
        code:
`export function quicksort<T>(
  arr: T[],
  compare: (a: T, b: T) => number = (a, b) => (a < b ? -1 : 1)
): T[] {
  if (arr.length <= 1) return arr;
  const [pivot, ...rest] = arr;
  const left = rest.filter(x => compare(x, pivot) < 0);
  const right = rest.filter(x => compare(x, pivot) >= 0);
  return [...quicksort(left, compare), pivot, ...quicksort(right, compare)];
}`
      },
      explain: {
        note:'已解释快速排序的算法思路',
        stats:{lines:'—', tests:'—', time:'0.3'},
        text:
`**快速排序**是分治算法：

- 选基准 \`pivot\`，把数组分成「小于」与「大于等于」两部分；
- 对两半**递归**排序后拼接；
- 平均 **O(n log n)**，最坏 O(n²)（已排序且选首元素时）。

示例实现用 \`filter\` 表达分区，简洁但额外开辟了空间。`
      }
    },

    crud: {
      gen: {
        note:'已生成 REST 控制器（user.controller.ts）',
        stats:{lines:22, tests:'10/10', time:'1.5'},
        code:
`import { Request, Response } from 'express';
import { UserService } from './user.service';

export class UserController {
  constructor(private svc: UserService) {}

  list = async (_req: Request, res: Response) => {
    res.json(await this.svc.findAll());
  };

  get = async (req: Request, res: Response) => {
    const u = await this.svc.findById(req.params.id);
    u ? res.json(u) : res.status(404).json({ error: 'not found' });
  };
}`
      },
      refactor: {
        note:'重构建议：抽服务层、统一错误处理',
        stats:{lines:18, tests:'10/10', time:'1.0'},
        improvements:['逻辑下沉到 Service，控制器只做 IO','统一 \`handle\` 包裹异常','参数校验前置'],
        code:
`import { Request, Response } from 'express';
import { UserService } from './user.service';

const handle = (fn: (r: Request, res: Response) => Promise<void>) =>
  async (req: Request, res: Response) => {
    try { await fn(req, res); }
    catch (e) { res.status(500).json({ error: (e as Error).message }); }
  };

export class UserController {
  constructor(private svc: UserService) {}
  list = handle(async (_q, res) => { res.json(await this.svc.findAll()); });
  get = handle(async (req, res) => {
    const u = await this.svc.findById(req.params.id);
    u ? res.json(u) : res.status(404).json({ error: 'not found' });
  });
}`
      },
      explain: {
        note:'已解释 REST 控制器的职责边界',
        stats:{lines:'—', tests:'—', time:'0.3'},
        text:
`该控制器遵循 **瘦控制器 / 胖服务** 原则：

- 控制器只负责**解析请求、调用服务、组装响应**；
- 业务逻辑（查库、规则）全部在 \`UserService\`；
- \`list\` / \`get\` 用箭头函数绑定 \`this\`，便于直接挂到路由。`
      }
    },

    default: {
      gen: {
        note:'已根据描述生成函数骨架',
        stats:{lines:7, tests:'3/3', time:'0.9'},
        code:
`// 依据任务描述生成的可运行骨架
export function solution(input: unknown) {
  /**
   * TODO: 在此实现核心逻辑
   * 输入：input
   * 输出：处理结果
   */
  return input;
}`
      },
      refactor: {
        note:'重构建议：明确入参类型与返回语义',
        stats:{lines:9, tests:'3/3', time:'0.7'},
        improvements:['补充类型签名','拆分过长表达式为命名步骤','增加文档注释'],
        code:
`// 重构后：类型清晰、步骤可读
export function solution<T>(input: T): T {
  const normalized = normalize(input);
  const result = transform(normalized);
  return result;
}

const normalize = <T>(x: T) => x;
const transform = <T>(x: T) => x;`
      },
      explain: {
        note:'已解释该代码段',
        stats:{lines:'—', tests:'—', time:'0.3'},
        text:
`这段代码是一个**通用处理骨架**：接收 \`input\`，经过归一化与转换后返回。

- 当前为占位实现，需在 \`normalize\` / \`transform\` 中补充真实逻辑；
- 泛型 \`<T>\` 保持输入输出类型一致，调用处可获得类型提示。`
      }
    }
  };

  /* ---------- MCP 工具调用链文案 ---------- */
  function mcpChain(kind){
    if(kind === 'gen') return [
      ['read_file', 'src/auth.ts'],
      ['read_file', 'src/server.ts'],
      ['write_file', 'src/middleware/auth.ts'],
      ['run_tests', '✓ 12 passed'],
      ['open_pr', 'feat/auth-guard']
    ];
    if(kind === 'refactor') return [
      ['read_file', 'src/auth.ts'],
      ['grep_symbol', 'authGuard'],
      ['write_file', 'src/auth.ts'],
      ['run_tests', '✓ 12 passed']
    ];
    return [
      ['read_file', 'src/middleware/auth.ts'],
      ['search_symbol', 'jwt.verify'],
      ['get_doc', 'jsonwebtoken']
    ];
  }
  function mcpCls(tool){
    if(/read|grep|search|get_doc/.test(tool)) return 'c-dim';
    if(/write/.test(tool)) return 'c-acc';
    if(/run_tests/.test(tool)) return 'c-ok';
    return 'c-acc';
  }

  /* ---------- 渲染产出卡 ---------- */
  let currentCode = '';
  function renderOutput(kind, sc){
    const r = RESPONSES[sc][kind];
    const out = $('output');
    if(kind === 'explain'){
      currentCode = r.text;
      out.innerHTML = '<div style="font-size:14px;line-height:1.85;color:var(--text)">' + window.md(r.text) + '</div>';
    } else {
      currentCode = r.code;
      let html = '<div style="font-size:12.5px;color:var(--text-dim);margin-bottom:10px">' + window.esc(r.note) + '</div>';
      html += '<pre class="code">' + highlight(r.code) + '</pre>';
      if(r.improvements){
        html += '<div style="margin-top:12px;font-size:12px;color:var(--text-mute)">重构要点：</div><div class="chips" style="margin-top:8px">';
        r.improvements.forEach(i => html += '<span class="opt on" style="cursor:default">' + window.esc(i) + '</span>');
        html += '</div>';
      }
      out.innerHTML = html;
    }
    $('outSub').textContent = { gen:'生成代码', refactor:'重构后代码', explain:'自然语言解释' }[kind];
    // 更新统计
    $('stLines').textContent = r.stats.lines;
    $('stTests').textContent = r.stats.tests;
    $('stTime').textContent = r.stats.time;
  }

  /* ---------- 动画：生成过程终端 + MCP 链 ---------- */
  async function animate(kind, sc){
    const term = $('genTerm');
    const r = RESPONSES[sc][kind];
    const lines = [
      '^acc 意图识别: ' + INTENT[kind],
      '^acc 路由到 skill:' + SKILL[kind],
      '^dim 拼接上下文: 2 files (src/auth.ts, src/server.ts)'
    ];
    if(kind === 'explain'){
      lines.push('^ok 检索符号与文档…');
      lines.push('^ok 生成自然语言解释…');
    } else {
      lines.push('^ok LLM 流式生成中…');
      r.code.split('\n').forEach(l => lines.push(l));
    }
    await window.typeLines(term, lines, { speed:5, pause:22 });

    // MCP 调用链
    const mcp = $('mcpTerm');
    mcp.innerHTML = '';
    const chain = mcpChain(kind);
    for(const [tool, arg] of chain){
      window.termLine(mcp, '→ ' + tool + '  ' + arg, mcpCls(tool));
      await window.wait(160);
    }
  }

  /* ---------- 主动作 ---------- */
  let busy = false;
  async function runAction(kind){
    const task = $('task').value.trim();
    if(!task) return window.toast('请输入任务描述');
    if(busy) return;
    busy = true;
    const sc = pickScenario(task);
    try { await animate(kind, sc); }
    finally { renderOutput(kind, sc); busy = false; }
  }

  /* ---------- 流水线演示 ---------- */
  const PIPE = ['p1','p2','p3','p4','p5'];
  const PIPE_DESC = ['识别为 编码任务', 'skill:' + SKILL.gen, '检索 2 个文件', '流式生成中', 'read_file→run_tests'];
  function wire(){
    $('btnGen').onclick = () => runAction('gen');
    $('btnRefactor').onclick = () => runAction('refactor');
    $('btnExplain').onclick = () => runAction('explain');

    $$('#samples .opt').forEach(b => b.onclick = () => {
      $('task').value = b.dataset.q;
      $$('#samples .opt').forEach(x => x.classList.remove('on'));
      b.classList.add('on');
    });

    $('copyBtn').onclick = () => {
      if(!currentCode) return window.toast('暂无可复制内容');
      const done = () => window.toast('已复制到剪贴板');
      if(navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(currentCode).then(done).catch(()=>fallbackCopy(currentCode, done));
      } else fallbackCopy(currentCode, done);
    };

    $('runPipe').onclick = async () => {
      await window.runPipeline(PIPE, {
        delay:520,
        onStep:(i) => window.setStageDesc(PIPE[i], PIPE_DESC[i])
      });
    };

    $('fillSample').onclick = () => {
      $('task').value = '为 Express 写一个 JWT 鉴权中间件';
      window.toast('已填充示例任务');
    };
  }
  function fallbackCopy(text, done){
    const ta = document.createElement('textarea');
    ta.value = text; ta.style.position='fixed'; ta.style.opacity='0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); done(); } catch { window.toast('复制失败'); }
    document.body.removeChild(ta);
  }

  /* ---------- 启动 ---------- */
  function start(){
    wire();
    // hero KV 数字动画
    if($('kvLang')) window.countUp($('kvLang'), 8);
    if($('kvCap')) window.countUp($('kvCap'), 4);
    if($('kvMcp')) window.countUp($('kvMcp'), 12);
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

  window.boot();
})();
