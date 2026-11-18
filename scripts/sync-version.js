import fs from 'fs';
import path from 'path';

// 使用 process.cwd() 获取项目根目录，完美适配 ESM 且避免 __dirname 兼容问题
const rootDir = process.cwd();

// 1. 读取根目录 package.json 中由 changesets 刚刚升级后的新版本号
const rootPkgPath = path.join(rootDir, 'package.json');
if (!fs.existsSync(rootPkgPath)) {
    console.error('错误: 未找到根目录的 package.json');
    process.exit(1);
}

const rootPkg = JSON.parse(fs.readFileSync(rootPkgPath, 'utf8'));
const newVersion = rootPkg.version;

console.log(`[Version Sync] 正在将全局新版本号同步到后端: ${newVersion}`);

// 2. 同步更新后端 backend/pyproject.toml 中的 version
const pyProjectPath = path.join(rootDir, 'backend/pyproject.toml');
if (fs.existsSync(pyProjectPath)) {
    let pyContent = fs.readFileSync(pyProjectPath, 'utf8');
    
    // 使用正则精准匹配 pyproject.toml 中的 version = "x.x.x"
    const newPyContent = pyContent.replace(/^version\s*=\s*["'].*?["']/m, `version = "${newVersion}"`);
    
    if (pyContent === newPyContent) {
        console.warn('[Version Sync] 警告: 未能在 backend/pyproject.toml 中匹配到 version 字段');
    } else {
        fs.writeFileSync(pyProjectPath, newPyContent, 'utf8');
        console.log('[Version Sync] 成功更新 backend/pyproject.toml 版本号！');
    }
} else {
    console.warn('[Version Sync] 警告: 未找到 backend/pyproject.toml 文件');
}