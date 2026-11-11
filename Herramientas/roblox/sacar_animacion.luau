-- Saca una animacion de Roblox Studio a JSON para Herramientas/blender/animacion_roblox.py (correr con execute_luau).
-- Pega este archivo una vez; despues:
--   _G.CL_sacarAnim(workspace.MiPersonaje, "Paso_Yamal")  -> JSON (copiarlo a Personajes/Animaciones/Paso_Yamal.json)
-- Busca, en este orden: un CurveAnimation dentro del personaje (lo crea el Animation Editor al importar un ID),
-- un KeyframeSequence dentro del personaje o en ServerStorage.RBX_ANIMSAVES.<personaje>, o un objeto Animation con
-- su AnimationId (solo baja animaciones tuyas o de Roblox: las de otros las bloquea Roblox).
-- Formato: tiempos en milisegundos y valores x1000 (enteros) para que el texto sea corto. No modifica nada.
local HS = game:GetService("HttpService")

local function curvaJSON(clip, nombre)
	local T, Tidx, J, dur = {}, {}, {}, 0
	local function canal(fc)
		if not fc then return 0 end
		local k = fc:GetKeys()
		if #k == 0 then return 0 end
		local ts, vs = {}, {}
		for _, key in ipairs(k) do
			table.insert(ts, math.floor(key.Time * 1000 + 0.5)); table.insert(vs, math.floor(key.Value * 1000 + 0.5))
			dur = math.max(dur, key.Time)
		end
		local sig = table.concat(ts, ",")
		if not Tidx[sig] then table.insert(T, ts); Tidx[sig] = #T end
		return {Tidx[sig], vs}
	end
	local function xyz(c) return {canal(c:FindFirstChild("X")), canal(c:FindFirstChild("Y")), canal(c:FindFirstChild("Z"))} end
	for _, f in ipairs(clip:GetDescendants()) do
		if f:IsA("Folder") then
			local p, r = f:FindFirstChild("Position"), f:FindFirstChild("Rotation")
			if p or r then
				local e = {padre = f.Parent:IsA("Folder") and f.Parent.Name or nil}
				if p then e.p = xyz(p) end
				if r then e.r = xyz(r); e.orden = (tostring(r.RotationOrder):gsub("Enum.RotationOrder.", "")) end
				J[f.Name] = e
			end
		end
	end
	return {nombre = nombre, fuente = clip:GetFullName(), loop = clip.Loop, dur = dur, escala = 1000, T = T, J = J}
end

-- KeyframeSequence: una llave por Keyframe (interpolacion lineal; los easings de Roblox se aproximan)
local function kfsJSON(kfs, nombre)
	local kfs_ = kfs:GetKeyframes()
	table.sort(kfs_, function(a, b) return a.Time < b.Time end)
	local ts, canales, padres, dur = {}, {}, {}, 0
	for i, kf in ipairs(kfs_) do
		table.insert(ts, math.floor(kf.Time * 1000 + 0.5)); dur = math.max(dur, kf.Time)
		for _, pose in ipairs(kf:GetDescendants()) do
			if pose:IsA("Pose") and pose.Parent:IsA("Pose") then
				local n = pose.Name
				canales[n] = canales[n] or {p = {{}, {}, {}}, r = {{}, {}, {}}}
				padres[n] = pose.Parent.Name
				local cf = pose.CFrame
				local rx, ry, rz = cf:ToEulerAnglesXYZ()
				local c = canales[n]
				for k, v in ipairs({cf.X, cf.Y, cf.Z}) do c.p[k][i] = v end
				for k, v in ipairs({rx, ry, rz}) do
					local prev = c.r[k][i - 1]
					if prev then while v - prev > math.pi do v -= 2 * math.pi end while v - prev < -math.pi do v += 2 * math.pi end end
					c.r[k][i] = v
				end
			end
		end
	end
	local J = {}
	for n, c in pairs(canales) do
		local function lista(vals)
			local out, alguno = {}, false
			-- keyframes donde esta articulacion no tiene Pose: se interpola entre sus vecinos (antes se ponia 0 = pose de
			-- descanso y la pieza "brincaba"; 2026-11-11)
			local llenos = {}
			for i = 1, #ts do if vals[i] ~= nil then table.insert(llenos, i) end end
			local function valor(i)
				if vals[i] ~= nil or #llenos == 0 then return vals[i] or 0 end
				local a, b
				for _, j in ipairs(llenos) do if j < i then a = j elseif j > i and not b then b = j end end
				if not a then return vals[b] end
				if not b then return vals[a] end
				local f = (ts[i] - ts[a]) / math.max(1, ts[b] - ts[a])
				return vals[a] + (vals[b] - vals[a]) * f
			end
			for i = 1, #ts do local v = valor(i); if math.abs(v) > 1e-4 then alguno = true end; out[i] = math.floor(v * 1000 + 0.5) end
			return alguno and {1, out} or 0
		end
		J[n] = {padre = padres[n], orden = "XYZ", p = {lista(c.p[1]), lista(c.p[2]), lista(c.p[3])}, r = {lista(c.r[1]), lista(c.r[2]), lista(c.r[3])}}
	end
	return {nombre = nombre, fuente = kfs:GetFullName(), loop = kfs.Loop, dur = dur, escala = 1000, T = {ts}, J = J}
end

_G.CL_sacarAnim = function(modelo, nombre, clip)
	-- clip (opcional, 2026-11-11): nombre de UNA animacion guardada en ServerStorage.RBX_ANIMSAVES.<personaje>
	-- (cuando el usuario guardo varias: "Walk Ciervo", "Run Ciervo"...). Tambien se puede pasar el KeyframeSequence directo.
	if modelo:IsA("KeyframeSequence") then return HS:JSONEncode(kfsJSON(modelo, nombre or modelo.Name)) end
	nombre = nombre or modelo.Name
	if clip then
		local saves = game:GetService("ServerStorage"):FindFirstChild("RBX_ANIMSAVES")
		local k = saves and saves:FindFirstChild(modelo.Name) and saves[modelo.Name]:FindFirstChild(clip)
		if not k then return "NO ENCONTRE la animacion guardada '" .. clip .. "' de " .. modelo.Name end
		return HS:JSONEncode(kfsJSON(k, nombre))
	end
	for _, c in ipairs(modelo:GetChildren()) do
		if c:IsA("CurveAnimation") then return HS:JSONEncode(curvaJSON(c, nombre)) end
	end
	local kfs = modelo:FindFirstChildWhichIsA("KeyframeSequence", true)
	local saves = game:GetService("ServerStorage"):FindFirstChild("RBX_ANIMSAVES")
	if not kfs and saves and saves:FindFirstChild(modelo.Name) then
		kfs = saves[modelo.Name]:FindFirstChildWhichIsA("KeyframeSequence", true)
	end
	if not kfs then
		local anim = modelo:FindFirstChildWhichIsA("Animation", true)
		if anim and anim.AnimationId ~= "" then
			local ok, res = pcall(function()
				return game:GetService("KeyframeSequenceProvider"):GetKeyframeSequenceAsync(anim.AnimationId)
			end)
			if ok then kfs = res else return "NO SE PUDO BAJAR " .. anim.AnimationId .. ": " .. tostring(res) end
		end
	end
	if kfs then return HS:JSONEncode(kfsJSON(kfs, nombre)) end
	return "SIN ANIMACION en " .. modelo:GetFullName() .. " (importala con el Animation Editor o pon un objeto Animation con su ID)"
end

return "listo: _G.CL_sacarAnim(modelo, nombre)"
