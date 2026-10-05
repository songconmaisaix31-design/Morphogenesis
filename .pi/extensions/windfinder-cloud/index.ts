import { execFile } from "node:child_process";
import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const MODEL_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$/;
const DEFAULT_MODEL = "qwen3.7-max";
const BL_TIMEOUT_MS = 320_000;

const CLOUD_MODELS: Array<{ id: string; purpose: string }> = [
  { id: "qwen3.8-max", purpose: "最新旗舰通用对话与推理模型" },
  { id: "qwen3.7-max", purpose: "默认通用对话模型，能力与成本平衡" },
  { id: "qwen-max", purpose: "经典旗舰通用大模型" },
  { id: "qwen3.5-max", purpose: "通用对话与推理模型" },
  { id: "qwen-coder-plus", purpose: "代码生成与编程任务专用模型" },
  { id: "qwen3-coder-plus", purpose: "qwen3 系列代码生成与编程专用模型" },
];

function shellQuote(value: string): string {
  if (process.platform === "win32") {
    return '"' + value.replace(/"/g, '""') + '"';
  }
  return "'" + value.replace(/'/g, "'\\''") + "'";
}

function scrub(value: string): string {
  return String(value ?? "")
    .replace(/sk-[A-Za-z0-9_-]{8,}/g, "***")
    .replace(/\b[A-Za-z0-9_-]{32,}\b/g, "***")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 200);
}

function runBl(args: string[]): Promise<{ error: Error | null; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    execFile(
      "bl",
      args,
      { shell: true, timeout: BL_TIMEOUT_MS, maxBuffer: 8 * 1024 * 1024 },
      (error, stdout, stderr) => {
        resolve({ error, stdout: String(stdout ?? ""), stderr: String(stderr ?? "") });
      },
    );
  });
}

const cloudComputeTool = defineTool({
  name: "cloud_compute",
  label: "Cloud Compute",
  description:
    "Run a prompt on an Aliyun Bailian (DashScope) cloud model via the `bl` CLI and return the assistant reply text.",
  parameters: Type.Object({
    model: Type.Optional(
      Type.String({
        description: "DashScope model id (e.g. qwen3.8-max, qwen3.7-max, qwen-max). Defaults to qwen3.7-max.",
      }),
    ),
    message: Type.String({ description: "User message / prompt text to send to the model." }),
    system: Type.Optional(Type.String({ description: "Optional system prompt." })),
  }),

  async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
    const model =
      typeof params.model === "string" && params.model.length > 0 ? params.model : DEFAULT_MODEL;
    if (!MODEL_PATTERN.test(model)) {
      return {
        content: [{ type: "text", text: "cloud_compute error: invalid model id" }],
        details: { error: "invalid model id", model },
      };
    }

    const message = String(params.message ?? "");
    if (message.trim().length === 0) {
      return {
        content: [{ type: "text", text: "cloud_compute error: message is empty" }],
        details: { error: "message is empty", model },
      };
    }

    const args = [
      "--timeout",
      "300",
      "text",
      "chat",
      "--model",
      model,
      "--message",
      shellQuote(message),
    ];
    if (typeof params.system === "string" && params.system.trim().length > 0) {
      args.push("--system", shellQuote(params.system));
    }
    args.push("--output", "json");

    const { error, stdout, stderr } = await runBl(args);

    if (error) {
      let reason = "cloud call failed";
      try {
        const errObj = JSON.parse(stderr) as { error?: { message?: string } };
        if (errObj && errObj.error && errObj.error.message) {
          reason = scrub(errObj.error.message) || reason;
        }
      } catch {
        // keep the generic reason
      }
      return {
        content: [{ type: "text", text: `cloud_compute error: ${reason}` }],
        details: { error: reason, model },
      };
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(stdout);
    } catch {
      return {
        content: [{ type: "text", text: "cloud_compute error: invalid response from cloud" }],
        details: { error: "invalid response from cloud", model },
      };
    }

    const obj = parsed as {
      error?: { message?: string };
      choices?: Array<{ message?: { content?: string } }>;
    };

    if (obj && obj.error) {
      const reason = scrub(obj.error.message || "upstream error");
      return {
        content: [{ type: "text", text: `cloud_compute error: ${reason}` }],
        details: { error: reason, model },
      };
    }

    const content = obj?.choices?.[0]?.message?.content;
    if (typeof content !== "string" || content.length === 0) {
      return {
        content: [{ type: "text", text: "cloud_compute error: empty model reply" }],
        details: { error: "empty model reply", model },
      };
    }

    return {
      content: [{ type: "text", text: content }],
      details: { model, content },
    };
  },
});

const listCloudModelsTool = defineTool({
  name: "list_cloud_models",
  label: "List Cloud Models",
  description: "List available Qwen cloud (DashScope) models and a one-line purpose for each.",
  parameters: Type.Object({}),

  async execute(_toolCallId, _params, _signal, _onUpdate, _ctx) {
    const text = CLOUD_MODELS.map((m) => `- ${m.id}: ${m.purpose}`).join("\n");
    return {
      content: [{ type: "text", text }],
      details: { models: CLOUD_MODELS },
    };
  },
});

export default function (pi: ExtensionAPI) {
  pi.registerTool(cloudComputeTool);
  pi.registerTool(listCloudModelsTool);
}
