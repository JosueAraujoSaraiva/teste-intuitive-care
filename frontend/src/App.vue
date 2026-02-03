<template>
  <div style="max-width: 1100px; margin: 0 auto; padding: 16px; font-family: Arial, sans-serif;">
    <header style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:16px;">
      <h2 style="margin:0;">IntuitiveCare – MVP Vue</h2>
      <nav style="display:flex; gap:12px;">
        <RouterLink to="/operadoras">Operadoras</RouterLink>
      </nav>
    </header>

    <RouterView />
  </div>
</template>

<script setup>
</script>

<style scoped>
a { text-decoration: none; }
a.router-link-active { font-weight: 700; }
</style>
